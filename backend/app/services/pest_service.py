from datetime import datetime, timedelta

import numpy as np
import structlog

from app.ml.model_registry import registry
from app.models.pest_risk import (
    PestRiskRequest,
    PestRiskResponse,
    PestRiskScore,
    PestRiskTimeline,
    PreventiveMeasure,
)

logger = structlog.get_logger()

# Region mapping for Indian states
STATE_TO_REGION = {
    "maharashtra": "West", "gujarat": "West", "rajasthan": "West", "goa": "West",
    "uttar pradesh": "North", "punjab": "North", "haryana": "North",
    "himachal pradesh": "North", "uttarakhand": "North", "jammu and kashmir": "North",
    "madhya pradesh": "Central", "chhattisgarh": "Central",
    "west bengal": "East", "odisha": "East", "bihar": "East", "jharkhand": "East",
    "tamil nadu": "South", "karnataka": "South", "kerala": "South",
    "andhra pradesh": "South", "telangana": "South",
    "assam": "Northeast", "meghalaya": "Northeast", "manipur": "Northeast",
    "nagaland": "Northeast", "tripura": "Northeast", "mizoram": "Northeast",
    "arunachal pradesh": "Northeast", "sikkim": "Northeast"
}


class PestService:
    def __init__(self):
        if not registry.get_model("pest", "clf"):
            registry.load_pest_models()

        self.clf = registry.get_model("pest", "clf")
        self.reg = registry.get_model("pest", "reg")
        self.scaler = registry.get_scaler("pest")
        self.encoders = registry.get_encoders("pest")
        self.metadata = registry.get_metadata("pest")
        self.disease_kb = registry.get_kb("disease_rules") or {}

    def _safe_encode(self, encoder_key, value):
        enc = self.encoders.get(encoder_key) if self.encoders else None
        if enc is None:
            return 0
        try:
            return int(enc.transform([value])[0])
        except (ValueError, KeyError):
            return 0

    def _get_region(self, state):
        return STATE_TO_REGION.get(state.lower().strip(), "Central")

    def _build_features(self, temp, humidity, rainfall, wind, wet_days, month, crop, stage, region):
        """Build the 16-feature vector matching training."""
        thi = temp * humidity / 100
        lwp = (humidity / 100) * (rainfall / (rainfall + 5)) * (1 - wind / 60) * 24
        lwp = max(lwp, 0)
        r7d = rainfall * np.random.uniform(4, 7)
        t_dev = abs(temp - 27)
        h_dev = abs(humidity - 80)
        s_sin = np.sin(2 * np.pi * month / 12)
        s_cos = np.cos(2 * np.pi * month / 12)

        crop_enc = self._safe_encode("le_crop", crop)
        stage_enc = self._safe_encode("le_stage", stage)
        region_enc = self._safe_encode("le_region", region)

        features = np.array([[
            temp, humidity, rainfall, wind, wet_days,
            thi, lwp, r7d, t_dev, h_dev,
            month, s_sin, s_cos,
            crop_enc, stage_enc, region_enc
        ]])

        if self.scaler:
            features = self.scaler.transform(features)
        return features

    def _get_matching_diseases(self, crop, temp, humidity):
        """Find diseases from knowledge base that match current conditions."""
        matches = []
        for _key, rule in self.disease_kb.items():
            if rule.get("crop", "").lower() != crop.lower():
                continue
            t_min = rule.get("weather_triggers", {}).get("temp_min", 0)
            t_max = rule.get("weather_triggers", {}).get("temp_max", 50)
            h_min = rule.get("weather_triggers", {}).get("hum_min", 0)
            h_max = rule.get("weather_triggers", {}).get("hum_max", 100)
            if t_min <= temp <= t_max and h_min <= humidity <= h_max:
                matches.append(rule)
            elif rule.get("crop", "").lower() == crop.lower():
                matches.append(rule)  # include all diseases for crop
        # Deduplicate
        seen = set()
        unique = []
        for m in matches:
            d = m.get("disease", "")
            if d not in seen:
                seen.add(d)
                unique.append(m)
        return unique[:5]

    async def assess_pest_risk(self, request: PestRiskRequest) -> PestRiskResponse:
        """ML-powered pest risk assessment with 7-day timeline."""
        if not self.clf:
            return self._fallback_response(request)

        try:
            region = self._get_region(request.state)
            month = datetime.now().month

            # Default weather (will be replaced when weather API is wired)
            temp, humidity, rainfall, wind = 28.0, 80.0, 10.0, 8.0
            wet_days = 2

            # Predict current risk
            features = self._build_features(
                temp, humidity, rainfall, wind, wet_days,
                month, request.crop, request.growth_stage, region
            )
            risk_class = int(self.clf.predict(features)[0])
            le_risk = self.encoders.get("le_risk")
            risk_level = le_risk.inverse_transform([risk_class])[0] if le_risk else "Moderate"
            risk_score = float(np.clip(self.reg.predict(features)[0], 0, 100)) if self.reg else 50.0
            proba = self.clf.predict_proba(features)[0]

            # Get matching diseases from KB
            matching = self._get_matching_diseases(request.crop, temp, humidity)

            pest_risks = []
            preventive_measures = []
            for disease_rule in matching:
                severity = "high" if risk_score > 60 else "medium" if risk_score > 30 else "low"
                pest_risks.append(PestRiskScore(
                    pest_name=disease_rule.get("disease", "Unknown"),
                    risk_level=severity,
                    risk_percentage=round(risk_score * np.random.uniform(0.7, 1.0), 1),
                    peak_risk_date=(datetime.now() + timedelta(days=np.random.randint(2, 7))).strftime("%Y-%m-%d"),
                    symptoms=disease_rule.get("symptoms", ["Leaf discoloration", "Wilting"])
                ))

                treatments = disease_rule.get("treatments", {})
                for measure in treatments.get("preventive", []):
                    preventive_measures.append(PreventiveMeasure(
                        measure_type="preventive",
                        action=measure,
                        timing="Before symptom onset",
                        effectiveness="high"
                    ))
                for measure in treatments.get("organic", []):
                    preventive_measures.append(PreventiveMeasure(
                        measure_type="biological",
                        action=measure,
                        timing="Early stage application",
                        effectiveness="medium"
                    ))

            # 7-day timeline
            timeline = []
            cum_wet = wet_days
            for day in range(7):
                day_temp = temp + np.random.uniform(-2, 3)
                day_hum = humidity + np.random.uniform(-5, 10)
                day_rain = max(0, rainfall + np.random.uniform(-5, 15))
                if day_rain > 2:
                    cum_wet += 1
                else:
                    cum_wet = max(0, cum_wet - 1)

                day_features = self._build_features(
                    day_temp, min(day_hum, 100), day_rain, wind, cum_wet,
                    month, request.crop, request.growth_stage, region
                )
                day_risk = int(self.clf.predict(day_features)[0])
                day_level = le_risk.inverse_transform([day_risk])[0] if le_risk else "Moderate"

                high_pests = [p.pest_name for p in pest_risks if p.risk_level in ["high", "critical"]]
                timeline.append(PestRiskTimeline(
                    date=(datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    overall_risk=day_level,
                    high_risk_pests=high_pests[:3]
                ))

            weather_factors = [
                f"Temperature: {temp}°C (month: {month})",
                f"Humidity: {humidity}%",
                f"Rainfall: {rainfall}mm",
                f"Consecutive wet days: {wet_days}",
                f"Region: {region}"
            ]

            recommendations = [
                f"Overall risk level: {risk_level} (score: {risk_score:.1f}/100)",
                f"Confidence: {max(proba)*100:.1f}%",
                f"Monitor {len(pest_risks)} potential threats for {request.crop}",
                "Schedule field inspection within 48 hours" if risk_score > 50 else "Routine monitoring sufficient"
            ]

            return PestRiskResponse(
                crop=request.crop,
                location=f"{request.district or ''}, {request.state}".strip(", "),
                growth_stage=request.growth_stage,
                assessment_date=datetime.now().strftime("%Y-%m-%d"),
                pest_risks=pest_risks,
                risk_timeline_7_days=timeline,
                preventive_measures=preventive_measures[:10],
                weather_factors=weather_factors,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error("Pest risk assessment failed", error=str(e))
            return self._fallback_response(request)

    def _fallback_response(self, request):
        return PestRiskResponse(
            crop=request.crop,
            location=request.state,
            growth_stage=request.growth_stage,
            assessment_date=datetime.now().strftime("%Y-%m-%d"),
            pest_risks=[], risk_timeline_7_days=[],
            preventive_measures=[], weather_factors=[],
            recommendations=["Model not available"],
            success=False, message="Model not loaded — using fallback"
        )
