import numpy as np
import pandas as pd
import structlog

from app.ml.model_registry import registry
from app.models.crop_recommend import (
    CropPrediction,
    CropRecommendRequest,
    CropRecommendResponse,
    SHAPExplanation,
)

logger = structlog.get_logger()


class CropService:
    def __init__(self):
        if not registry.get_model("crop"):
            registry.load_crop_models()

        self.model = registry.get_model("crop")
        self.scaler = registry.get_scaler("crop")
        self.label_encoder = registry.get_encoders("crop")
        self.metadata = registry.get_metadata("crop")
        if self.label_encoder:
            self.crops = list(self.label_encoder.classes_)
        else:
            self.crops = ["Rice", "Wheat", "Maize", "Cotton", "Tomato", "Potato", "Onion"]

    def _engineer_features(self, N, P, K, temperature, humidity, ph, rainfall, soil_type=None):
        """Replicate the feature engineering from training."""
        data = {
            "N": [N], "P": [P], "K": [K],
            "temperature": [temperature], "humidity": [humidity],
            "ph": [ph], "rainfall": [rainfall]
        }
        df = pd.DataFrame(data)

        # Engineered features (matching feature_engineering.py)
        df["N_P_ratio"] = df["N"] / (df["P"] + 1)
        df["N_K_ratio"] = df["N"] / (df["K"] + 1)
        df["P_K_ratio"] = df["P"] / (df["K"] + 1)
        df["NPK_total"] = df["N"] + df["P"] + df["K"]
        df["N_dominant"] = ((df["N"] > df["P"]) & (df["N"] > df["K"])).astype(int)
        df["P_dominant"] = ((df["P"] > df["N"]) & (df["P"] > df["K"])).astype(int)
        df["K_dominant"] = ((df["K"] > df["N"]) & (df["K"] > df["P"])).astype(int)
        df["temp_humidity_index"] = df["temperature"] * df["humidity"] / 100
        df["rainfall_temp_ratio"] = df["rainfall"] / (df["temperature"] + 1)
        df["aridity_index"] = df["temperature"] / (df["rainfall"] + 1)
        df["ph_deviation"] = abs(df["ph"] - 7.0)
        df["ph_category"] = pd.cut(df["ph"], bins=[-1, 5.5, 6.5, 7.5, 8.5, 15], labels=[0, 1, 2, 3, 4]).astype(int)
        df["rainfall_category"] = pd.cut(
            df["rainfall"], bins=[-1, 50, 100, 150, 200, 300, 10000],
            labels=[0, 1, 2, 3, 4, 5]
        ).astype(int)
        df["temp_zone"] = pd.cut(df["temperature"], bins=[-20, 15, 25, 35, 100], labels=[0, 1, 2, 3]).astype(int)

        # Tropical and nutrient scores (single-row normalization)
        t_norm = (temperature - 0) / (50 - 0 + 1e-8)
        h_norm = (humidity - 0) / (100 - 0 + 1e-8)
        r_norm = (rainfall - 0) / (500 - 0 + 1e-8)
        df["tropical_score"] = t_norm * 0.33 + h_norm * 0.33 + r_norm * 0.34

        n_norm = (N - 0) / (200 - 0 + 1e-8)
        p_norm = (P - 0) / (200 - 0 + 1e-8)
        k_norm = (K - 0) / (300 - 0 + 1e-8)
        df["nutrient_score"] = (n_norm + p_norm + k_norm) / 3

        # Soil type one-hot encoding
        soil_types = ["Black", "Clayey", "Loamy", "Red", "Sandy"]
        for s in soil_types:
            df[f"soil_{s}"] = 1 if soil_type and soil_type.value == s else 0

        # Ensure column order matches training
        feature_cols = self.metadata.get("feature_columns", [])
        if feature_cols:
            for col in feature_cols:
                if col not in df.columns:
                    df[col] = 0
            df = df[feature_cols]

        return df

    async def recommend_crops(self, request: CropRecommendRequest) -> CropRecommendResponse:
        """Real ML-powered crop recommendation."""
        if not self.model:
            logger.warning("Crop model not loaded, returning fallback")
            return self._fallback_response(request)

        try:
            # Build feature vector
            features_df = self._engineer_features(
                N=request.nitrogen, P=request.phosphorus, K=request.potassium,
                temperature=request.temperature, humidity=request.humidity,
                ph=request.ph, rainfall=request.rainfall,
                soil_type=request.soil_type
            )

            # Scale features
            features_scaled = self.scaler.transform(features_df.values) if self.scaler else features_df.values

            # Get probabilities for all classes
            probas = self.model.predict_proba(features_scaled)[0]

            # Top 5 crops
            top_indices = np.argsort(probas)[::-1][:5]
            predictions = []
            for idx in top_indices:
                crop_name = self.label_encoder.inverse_transform([idx])[0]
                predictions.append(CropPrediction(
                    crop_name=crop_name.capitalize(),
                    confidence=round(float(probas[idx]), 4),
                    suitability_score=round(float(probas[idx]) * 100, 1)
                ))

            # Real SHAP explanations using KernelExplainer
            import shap
            shap_explanation = []
            feature_names = ["nitrogen", "phosphorus", "potassium",
                             "temperature", "humidity", "ph", "rainfall"]
            feature_values = [request.nitrogen, request.phosphorus, request.potassium,
                              request.temperature, request.humidity, request.ph, request.rainfall]
            
            top_idx = top_indices[0]
            
            def predict_base(X):
                results = []
                for row in X:
                    d = self._engineer_features(row[0], row[1], row[2], row[3], row[4], row[5], row[6], request.soil_type)
                    s = self.scaler.transform(d.values) if self.scaler else d.values
                    results.append(self.model.predict_proba(s)[0][top_idx])
                return np.array(results)
                
            # Use a varied set of background points that fit exactly within the training bins
            bg = np.array([
                [10, 10, 10, 10, 30, 5.0, 40],
                [50, 50, 50, 25, 60, 6.5, 150],
                [100, 100, 100, 30, 80, 7.0, 250],
                [150, 150, 150, 35, 90, 7.5, 400],
                [190, 190, 290, 45, 95, 8.0, 490]
            ])
            explainer = shap.KernelExplainer(predict_base, bg)
            input_vals = np.array(feature_values).reshape(1, -1)
            
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                shap_vals = explainer.shap_values(input_vals, nsamples=30, silent=True)
                
            importances = shap_vals[0] if isinstance(shap_vals, list) else shap_vals[0]

            for name, val, imp in zip(feature_names, feature_values, importances, strict=False):
                shap_explanation.append(SHAPExplanation(
                    feature_name=name, importance=float(imp), value=val
                ))
            
            # Sort by absolute importance
            shap_explanation.sort(key=lambda x: abs(x.importance), reverse=True)

            # Recommendations
            top_crop = predictions[0].crop_name
            recommendations = [
                f"Top recommended crop: {top_crop} ({predictions[0].confidence*100:.1f}% confidence)",
                f"Soil pH of {request.ph} is {'optimal' if 6.0 <= request.ph <= 7.5 else 'suboptimal'} for {top_crop}",
                f"Nitrogen level ({request.nitrogen} kg/ha) is {'adequate' if request.nitrogen >= 80 else 'low — consider supplementation'}",
                f"Annual rainfall ({request.rainfall} mm) is {'sufficient' if request.rainfall >= 500 else 'limited — plan irrigation'}",
                f"Consider {predictions[1].crop_name} as alternative ({predictions[1].confidence*100:.1f}% confidence)"
            ]

            return CropRecommendResponse(
                predictions=predictions,
                shap_explanation=shap_explanation,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error("Crop prediction failed", error=str(e))
            return self._fallback_response(request)

    def _fallback_response(self, request):
        """Return a basic response when model isn't available."""
        return CropRecommendResponse(
            predictions=[CropPrediction(crop_name="Rice", confidence=0.5, suitability_score=50.0)],
            shap_explanation=[],
            recommendations=["Model not available. Please check server logs."],
            success=False,
            message="Model not loaded — using fallback"
        )
