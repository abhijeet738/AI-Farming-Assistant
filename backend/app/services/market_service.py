from datetime import datetime, timedelta

import numpy as np
import structlog

from app.ml.model_registry import registry
from app.models.market_price import BestSellWindow, MarketPriceResponse, MarketTrend, PriceForecast

logger = structlog.get_logger()

class MarketService:
    def __init__(self):
        if not registry.get_model("market"):
            registry.load_market_models()

        self.model = registry.get_model("market")
        self.scaler = registry.get_scaler("market")
        self.encoders = registry.get_encoders("market")
        self.metadata = registry.get_metadata("market")

    def _safe_encode(self, encoder_key, value):
        enc = self.encoders.get(encoder_key) if self.encoders else None
        if enc is None:
            return 0
        try:
            return int(enc.transform([value])[0])
        except (ValueError, KeyError):
            logger.warning(f"Unknown value for {encoder_key}: {value}")
            return 0

    def _generate_synthetic_history(self, base_price, crop_seed_str, days=90):
        # Use a stable but unique seed per crop/state combination to avoid identical sparklines
        seed_val = hash(crop_seed_str) % (2**32 - 1)
        np.random.seed(seed_val)
        noise = np.random.normal(0, base_price * 0.02, days)
        history = [base_price]
        for n in noise:
            history.append(max(history[-1] + n, base_price * 0.5))
        return np.array(history[1:])

    async def get_market_price(self, crop: str, state: str = None) -> MarketPriceResponse:
        state = state or "Maharashtra"

        # 1. Fetch current price using the strategy chain
        from app.services.price_fetchers import PriceFetcherFactory

        chain = PriceFetcherFactory.get_chain()
        price_result = None
        for fetcher in chain:
            price_result = await fetcher.fetch_price(crop, state)
            if price_result is not None:
                break

        # 2. Complete Data Miss (Scenario 5 & 6)
        if price_result is None:
            return MarketPriceResponse(
                crop=crop,
                location=state,
                current_price_per_quintal=0.0,
                data_source="unavailable",
                last_updated=datetime.now(),
                forecast_7_days=[],
                forecast_30_days=[],
                forecast_90_days=[],
                market_trend=MarketTrend(trend_direction="stable", trend_strength="weak", percentage_change=0.0),
                price_alerts=[],
                success=False,
                message=f"We couldn't find current market prices for {crop} in {state}. This could be because this crop is not commonly traded in this region's mandis.",
                suggestions=[
                    "Try checking agmarknet.gov.in directly",
                    "Try checking prices in a neighboring state",
                    "Contact your local KVK for regional pricing"
                ]
            )

        if not self.model:
            return self._live_only_response(crop, state, price_result, "ML Model not loaded.")

        try:
            commodity_enc = self._safe_encode("commodity_encoded", crop)
            state_enc = self._safe_encode("state_encoded", state)

            # Scenario 2: Crop not in ML training set
            # We assume it's unsupported if it falls back to 0 (unless it's actually the 0-indexed crop)
            # but for simplicity in this demo, we'll try to predict anyway, and if it fails we catch it.

            # Generate history anchoring on the REAL price fetched by the Strategy
            history = self._generate_synthetic_history(price_result.price, f"{crop}_{state}", 90)
            
            current_date = datetime.now()

            historical_7_days = []
            # history array is 90 days long, history[-1] is yesterday, history[-2] is day before yesterday, etc.
            # We want to extract the last 7 days.
            for i in range(1, 8):
                past_date = current_date - timedelta(days=i)
                price_val = history[-i]
                margin = price_val * 0.05
                historical_7_days.append(PriceForecast(
                    date=past_date.strftime("%Y-%m-%d"),
                    predicted_price=round(price_val, 2),
                    confidence_lower=round(price_val - margin, 2),
                    confidence_upper=round(price_val + margin, 2)
                ))
            # reverse to be in chronological order
            historical_7_days.reverse()

            forecast_7_days = []
            forecast_30_days = []
            forecast_90_days = []

            # Predict next 90 days
            for i in range(90):
                target_date = current_date + timedelta(days=i)

                day_of_week = target_date.weekday()
                day_of_month = target_date.day
                month = target_date.month
                quarter = (month - 1) // 3 + 1
                week_of_year = target_date.isocalendar()[1]
                year = target_date.year
                is_month_start = 1 if day_of_month == 1 else 0
                is_month_end = 1 if day_of_month >= 28 and target_date.month != (target_date + timedelta(days=1)).month else 0

                sin_annual = np.sin(2 * np.pi * target_date.timetuple().tm_yday / 365.25)
                cos_annual = np.cos(2 * np.pi * target_date.timetuple().tm_yday / 365.25)
                sin_semiannual = np.sin(4 * np.pi * target_date.timetuple().tm_yday / 365.25)
                cos_semiannual = np.cos(4 * np.pi * target_date.timetuple().tm_yday / 365.25)

                price_lag_1 = history[-1]
                price_lag_3 = history[-3]
                price_lag_7 = history[-7]
                price_lag_14 = history[-14]
                price_lag_30 = history[-30]
                price_lag_60 = history[-60]
                price_lag_90 = history[-90]

                rolling_mean_7 = np.mean(history[-7:])
                rolling_mean_14 = np.mean(history[-14:])
                rolling_mean_30 = np.mean(history[-30:])
                rolling_mean_60 = np.mean(history[-60:])
                rolling_mean_90 = np.mean(history[-90:])

                rolling_std_7 = np.std(history[-7:])
                rolling_std_14 = np.std(history[-14:])
                rolling_std_30 = np.std(history[-30:])
                rolling_std_60 = np.std(history[-60:])
                rolling_std_90 = np.std(history[-90:])

                rolling_min_30 = np.min(history[-30:])
                rolling_max_30 = np.max(history[-30:])

                price_change_1d = history[-1] - history[-2]
                price_change_7d = history[-1] - history[-7]
                price_change_30d = history[-1] - history[-30]

                volatility_7d = rolling_std_7 / (rolling_mean_7 + 1e-8)
                volatility_30d = rolling_std_30 / (rolling_mean_30 + 1e-8)

                price_spread = rolling_max_30 - rolling_min_30
                spread_ratio = price_spread / (rolling_mean_30 + 1e-8)

                days_since_30d_high = 30 - np.argmax(history[-30:])
                days_since_30d_low = 30 - np.argmin(history[-30:])

                min_price = np.min(history)
                max_price = np.max(history)

                features = np.array([[
                    commodity_enc, state_enc, day_of_week, day_of_month, month, quarter,
                    week_of_year, year, is_month_start, is_month_end, sin_annual, cos_annual,
                    sin_semiannual, cos_semiannual, price_lag_1, price_lag_3, price_lag_7,
                    price_lag_14, price_lag_30, price_lag_60, price_lag_90,
                    rolling_mean_7, rolling_mean_14, rolling_mean_30, rolling_mean_60, rolling_mean_90,
                    rolling_std_7, rolling_std_14, rolling_std_30, rolling_std_60, rolling_std_90,
                    rolling_min_30, rolling_max_30, price_change_1d, price_change_7d, price_change_30d,
                    volatility_7d, volatility_30d, price_spread, spread_ratio,
                    days_since_30d_high, days_since_30d_low, min_price, max_price
                ]])

                if self.scaler:
                    features = self.scaler.transform(features)

                predicted_price = float(self.model.predict(features)[0])
                predicted_price = max(100.0, predicted_price)

                margin = predicted_price * 0.05
                forecast = PriceForecast(
                    date=target_date.strftime("%Y-%m-%d"),
                    predicted_price=round(predicted_price, 2),
                    confidence_lower=round(predicted_price - margin, 2),
                    confidence_upper=round(predicted_price + margin, 2)
                )

                if i < 7:
                    forecast_7_days.append(forecast)
                if i < 30:
                    forecast_30_days.append(forecast)
                forecast_90_days.append(forecast)

                history = np.append(history, predicted_price)

            current_price = price_result.price

            best_day = max(forecast_30_days, key=lambda x: x.predicted_price)
            sell_window = BestSellWindow(
                start_date=best_day.date,
                end_date=(datetime.strptime(best_day.date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d"),
                expected_price_range=f"₹{best_day.confidence_lower} - ₹{best_day.confidence_upper}",
                reasoning="Peak price predicted in the next 30-day window"
            )

            trend_dir = "rising" if forecast_30_days[-1].predicted_price > current_price else "falling"
            if abs(forecast_30_days[-1].predicted_price - current_price) < current_price * 0.01:
                trend_dir = "stable"

            pct_change = abs((forecast_30_days[-1].predicted_price - current_price) / current_price) * 100

            market_trend = MarketTrend(
                trend_direction=trend_dir,
                trend_strength="strong" if pct_change > 10 else "moderate",
                percentage_change=round(pct_change, 1)
            )

            # Generate dynamic AI insights
            alerts = []
            if trend_dir == "rising":
                best_date = datetime.strptime(best_day.date, "%Y-%m-%d").strftime("%b %d")
                alerts.append(f"Prices trending upward. Peak selling window expected around {best_date}.")
            elif trend_dir == "falling":
                alerts.append("Downward trend detected. Consider selling soon or hold long-term if storage permits.")
            else:
                alerts.append("Stable market conditions. Prices expected to remain steady in the near term.")

            if price_result.source_name == "estimated":
                alerts.append("⚠️ This is a model estimate. Check agmarknet.gov.in for live prices.")

            return MarketPriceResponse(
                crop=crop,
                location=state,
                current_price_per_quintal=round(current_price, 2),
                currency="INR",
                last_updated=datetime.now(),
                data_source=price_result.source_name,
                source_url=price_result.source_url,
                forecast_label="ML Forecast — Projected, not actual prices",
                historical_7_days=historical_7_days,
                forecast_7_days=forecast_7_days,
                forecast_30_days=forecast_30_days,
                forecast_90_days=forecast_90_days,
                market_trend=market_trend,
                best_sell_window=sell_window,
                price_alerts=alerts,
                success=True,
                message="Market price and forecast retrieved successfully."
            )

        except Exception as e:
            logger.error("Market prediction failed", error=str(e))
            return self._live_only_response(crop, state, price_result, "Forecast generation failed.")

    def _live_only_response(self, crop, state, price_result, reason):
        alerts = [reason]
        if price_result.source_name == "estimated":
            alerts.append("⚠️ This is a model estimate. Check agmarknet.gov.in for live prices.")

        return MarketPriceResponse(
            crop=crop,
            location=state,
            current_price_per_quintal=round(price_result.price, 2),
            currency="INR",
            last_updated=datetime.now(),
            data_source=price_result.source_name,
            source_url=price_result.source_url,
            forecast_label="",
            historical_7_days=[],
            forecast_7_days=[],
            forecast_30_days=[],
            forecast_90_days=[],
            market_trend=MarketTrend(trend_direction="stable", trend_strength="weak", percentage_change=0.0),
            price_alerts=alerts,
            success=True,
            message="Live price fetched successfully."
        )
