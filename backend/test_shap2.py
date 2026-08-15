import numpy as np
from app.services.crop_service import CropService
from app.models.crop_recommend import CropRecommendRequest
import shap

service = CropService()
request = CropRecommendRequest(
    nitrogen=85, phosphorus=78, potassium=83,
    temperature=28, humidity=46, ph=6.5, rainfall=33,
    soil_type="Loamy"
)
features_df = service._engineer_features(
    N=request.nitrogen, P=request.phosphorus, K=request.potassium,
    temperature=request.temperature, humidity=request.humidity,
    ph=request.ph, rainfall=request.rainfall,
    soil_type=request.soil_type
)
features_scaled = service.scaler.transform(features_df.values) if service.scaler else features_df.values
probas = service.model.predict_proba(features_scaled)[0]
top_indices = np.argsort(probas)[::-1][:5]
top_idx = top_indices[0]

def predict_base(X):
    results = []
    for row in X:
        d = service._engineer_features(row[0], row[1], row[2], row[3], row[4], row[5], row[6], request.soil_type)
        s = service.scaler.transform(d.values) if service.scaler else d.values
        results.append(service.model.predict_proba(s)[0][top_idx])
    return np.array(results)

bg = np.array([
    [0, 0, 0, 10, 30, 5.0, 50],
    [50, 50, 50, 25, 60, 6.5, 150],
    [100, 100, 100, 35, 80, 7.5, 300],
    [150, 150, 150, 40, 90, 8.0, 500],
    [200, 200, 300, 45, 100, 9.0, 1000]
])
explainer = shap.KernelExplainer(predict_base, bg)
feature_values = [request.nitrogen, request.phosphorus, request.potassium,
                  request.temperature, request.humidity, request.ph, request.rainfall]
input_vals = np.array(feature_values).reshape(1, -1)

try:
    shap_vals = explainer.shap_values(input_vals, nsamples=50)
    print("Success")
except Exception as e:
    print("Exception:", e)
