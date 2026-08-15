from app.ml.model_registry import registry
registry.load_crop_models()
model = registry.get_model("crop")
print(type(model))
if hasattr(model, "feature_importances_"):
    print("Has feature_importances_!")
    print(model.feature_importances_[:7])
