
import numpy as np
import structlog

from app.ml.model_registry import registry
from app.models.fertilizer import (
    ApplicationSchedule,
    FertilizerProduct,
    FertilizerRequest,
    FertilizerResponse,
    NPKDeficit,
)

logger = structlog.get_logger()

# Product catalog with costs
PRODUCT_DB = {
    "Urea":      {"npk": "46-0-0",   "cost": 6.5,  "method": "Broadcast and incorporate"},
    "DAP":       {"npk": "18-46-0",  "cost": 24.0, "method": "Basal application at sowing"},
    "MOP":       {"npk": "0-0-60",   "cost": 18.0, "method": "Basal application"},
    "10-26-26":  {"npk": "10-26-26", "cost": 22.0, "method": "Basal application"},
    "14-35-14":  {"npk": "14-35-14", "cost": 23.0, "method": "Basal application"},
    "17-17-17":  {"npk": "17-17-17", "cost": 20.0, "method": "Basal application"},
    "20-20":     {"npk": "20-20-0",  "cost": 18.0, "method": "Basal or top-dressing"},
    "28-28":     {"npk": "28-28-0",  "cost": 22.0, "method": "Top-dressing"},
}


class FertilizerService:
    def __init__(self):
        if not registry.get_model("fertilizer"):
            registry.load_fertilizer_models()

        self.model = registry.get_model("fertilizer")
        self.scaler = registry.get_scaler("fertilizer")
        self.encoders = registry.get_encoders("fertilizer")
        self.metadata = registry.get_metadata("fertilizer")
        self.crop_npk = registry.get_kb("crop_npk") or {}
        self.fertilizer_products = list(PRODUCT_DB.keys())

    def _safe_encode(self, encoder_key, value):
        enc = self.encoders.get(encoder_key) if self.encoders else None
        if enc is None:
            return 0
        try:
            return int(enc.transform([value])[0])
        except (ValueError, KeyError):
            logger.warning(f"Unknown value for {encoder_key}: {value}")
            return 0

    async def recommend_fertilizer(self, request: FertilizerRequest) -> FertilizerResponse:
        """Real ML-powered fertilizer recommendation."""
        if not self.model:
            return self._fallback_response(request)

        try:
            N, P, K = request.nitrogen, request.phosphorus, request.potassium
            temp = 27.0  # default ambient
            humidity = 65.0
            moisture = 35.0

            soil_enc = self._safe_encode("le_soil", "Loamy")  # default soil
            crop_enc = self._safe_encode("le_crop", request.crop)

            # Engineered features
            npk_total = N + P + K
            n_p_ratio = N / (P + 1)
            n_k_ratio = N / (K + 1)
            p_k_ratio = P / (K + 1)
            n_dominant = int(N > P and N > K)
            p_dominant = int(P > N and P > K)
            k_dominant = int(K > N and K > P)
            thi = temp * humidity / 100
            moisture_ratio = moisture / (humidity + 1)

            features = np.array([[
                temp, humidity, moisture, N, K, P,
                soil_enc, crop_enc,
                npk_total, n_p_ratio, n_k_ratio, p_k_ratio,
                n_dominant, p_dominant, k_dominant,
                thi, moisture_ratio
            ]])

            if self.scaler:
                features = self.scaler.transform(features)

            # Predict fertilizer class
            pred_class = int(self.model.predict(features)[0])
            le_fert = self.encoders.get("le_fertilizer")
            predicted_fertilizer = le_fert.inverse_transform([pred_class])[0] if le_fert else "Urea"

            # NPK analysis
            crop_req = self.crop_npk.get(request.crop, {"N": 120, "P": 60, "K": 40})
            if isinstance(crop_req, dict):
                req_n = crop_req.get("N", 120)
                req_p = crop_req.get("P", 60)
                req_k = crop_req.get("K", 40)
            else:
                req_n, req_p, req_k = 120, 60, 40

            n_deficit = max(0, req_n - N)
            p_deficit = max(0, req_p - P)
            k_deficit = max(0, req_k - K)
            total_req = req_n + req_p + req_k
            deficit_pct = ((n_deficit + p_deficit + k_deficit) / max(total_req, 1)) * 100

            npk_analysis = NPKDeficit(
                nitrogen_deficit=round(n_deficit, 1),
                phosphorus_deficit=round(p_deficit, 1),
                potassium_deficit=round(k_deficit, 1),
                deficit_percentage=round(deficit_pct, 1)
            )

            # Recommended products
            product_info = PRODUCT_DB.get(predicted_fertilizer, PRODUCT_DB["Urea"])
            qty = max(50, n_deficit * 2.17) if n_deficit > 0 else 100  # kg/ha
            cost = qty * product_info["cost"]

            recommended_products = [
                FertilizerProduct(
                    product_name=predicted_fertilizer,
                    npk_ratio=product_info["npk"],
                    quantity_kg_per_hectare=round(qty, 1),
                    cost_per_kg=product_info["cost"],
                    total_cost=round(cost, 2),
                    application_method=product_info["method"]
                )
            ]

            # Add supplementary if needed
            if p_deficit > 20:
                dap_qty = p_deficit * 2.17
                recommended_products.append(FertilizerProduct(
                    product_name="DAP", npk_ratio="18-46-0",
                    quantity_kg_per_hectare=round(dap_qty, 1),
                    cost_per_kg=24.0,
                    total_cost=round(dap_qty * 24, 2),
                    application_method="Basal application at sowing"
                ))

            if k_deficit > 20:
                mop_qty = k_deficit * 1.67
                recommended_products.append(FertilizerProduct(
                    product_name="MOP", npk_ratio="0-0-60",
                    quantity_kg_per_hectare=round(mop_qty, 1),
                    cost_per_kg=18.0,
                    total_cost=round(mop_qty * 18, 2),
                    application_method="Basal application"
                ))

            total_cost = sum(p.total_cost for p in recommended_products) * request.area_hectares

            # Schedule
            schedule = [
                ApplicationSchedule(
                    stage="basal", timing="At sowing/transplanting",
                    products=[p.product_name for p in recommended_products if "Basal" in p.application_method],
                    quantity_per_hectare=sum(p.quantity_kg_per_hectare for p in recommended_products) * 0.5
                ),
                ApplicationSchedule(
                    stage="top_dressing_1", timing="30 days after sowing",
                    products=[predicted_fertilizer],
                    quantity_per_hectare=qty * 0.3
                ),
                ApplicationSchedule(
                    stage="top_dressing_2", timing="60 days after sowing",
                    products=[predicted_fertilizer],
                    quantity_per_hectare=qty * 0.2
                )
            ]

            recommendations = [
                f"Predicted fertilizer: {predicted_fertilizer}",
                f"N deficit: {n_deficit:.0f} kg/ha | P deficit: {p_deficit:.0f} kg/ha | K deficit: {k_deficit:.0f} kg/ha",
                "Apply fertilizers in split doses for better nutrient uptake",
                "Consider soil testing every 2-3 years for accurate recommendations"
            ]

            return FertilizerResponse(
                crop=request.crop,
                area_hectares=request.area_hectares,
                npk_analysis=npk_analysis,
                recommended_products=recommended_products,
                application_schedule=schedule,
                total_cost_estimate=round(total_cost, 2),
                organic_alternatives=["Vermicompost", "Farmyard Manure", "Green Manure",
                                      "Biofertilizers (Rhizobium, PSB)", "Neem Cake"],
                recommendations=recommendations
            )

        except Exception as e:
            logger.error("Fertilizer prediction failed", error=str(e))
            return self._fallback_response(request)

    def _fallback_response(self, request):
        return FertilizerResponse(
            crop=request.crop, area_hectares=request.area_hectares,
            npk_analysis=NPKDeficit(nitrogen_deficit=0, phosphorus_deficit=0, potassium_deficit=0, deficit_percentage=0),
            recommended_products=[], application_schedule=[],
            total_cost_estimate=0, organic_alternatives=[], recommendations=["Model not available"],
            success=False, message="Model not loaded — using fallback"
        )
