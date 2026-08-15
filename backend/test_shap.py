import numpy as np
from app.ml.model_registry import registry
from app.services.crop_service import CropService
from app.models.crop_recommend import CropRecommendRequest
import shap

service = CropService()
request = CropRecommendRequest(
    nitrogen=15, phosphorus=20, potassium=27,
    temperature=28, humidity=24, ph=6.0, rainfall=33,
    soil_type="Clayey"
)

# Build features and predict
df = service._engineer_features(15, 20, 27, 28, 24, 6.0, 33, request.soil_type)
scaled = service.scaler.transform(df.values)
probas = service.model.predict_proba(scaled)[0]
top_idx = np.argsort(probas)[::-1][0]
print("Top crop:", service.label_encoder.inverse_transform([top_idx])[0])

def predict_base(X):
    results = []
    for row in X:
        d = service._engineer_features(row[0], row[1], row[2], row[3], row[4], row[5], row[6], request.soil_type)
        s = service.scaler.transform(d.values)
        results.append(service.model.predict_proba(s)[0][top_idx])
    return np.array(results)

bg = np.array([50, 50, 50, 25, 60, 6.5, 150]).reshape(1, -1)
explainer = shap.KernelExplainer(predict_base, bg)
input_vals = np.array([15, 20, 27, 28, 24, 6.0, 33]).reshape(1, -1)
shap_vals = explainer.shap_values(input_vals, nsamples=50)

print("SHAP:", shap_vals)
