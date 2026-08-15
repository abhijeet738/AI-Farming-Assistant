with open("backend/app/services/pest_service.py", "r") as f:
    content = f.read()

importances_code = """
            # SHAP Explanation
            import shap
            from app.models.crop_recommend import SHAPExplanation
            
            def predict_base(X):
                results = []
                for row in X:
                    f = self._build_features(
                        row[0], row[1], row[2], row[3], row[4],
                        month, request.crop, request.growth_stage, region
                    )
                    results.append(self.clf.predict_proba(f)[0][risk_class])
                return np.array(results)
                
            bg = np.array([
                [10, 30, 0, 0, 0],
                [25, 60, 50, 10, 2],
                [35, 80, 150, 20, 5],
                [45, 95, 300, 30, 10]
            ])
            explainer = shap.KernelExplainer(predict_base, bg)
            input_vals = np.array([temp, humidity, rainfall, wind, wet_days]).reshape(1, -1)
            
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                shap_vals = explainer.shap_values(input_vals, nsamples=30, silent=True)
                
            importances = shap_vals[0] if isinstance(shap_vals, list) else shap_vals[0]
            
            feature_names = ["temperature", "humidity", "rainfall", "wind_speed", "wet_days"]
            feature_values = [temp, humidity, rainfall, wind, wet_days]
            
            shap_explanation = []
            for name, val, imp in zip(feature_names, feature_values, importances, strict=False):
                shap_explanation.append(SHAPExplanation(
                    feature_name=name, importance=float(imp), value=float(val)
                ))
            shap_explanation.sort(key=lambda x: abs(x.importance), reverse=True)
            
            return PestRiskResponse(
                crop=request.crop,
                location=f"{request.district or ''}, {request.state}".strip(", "),
                growth_stage=request.growth_stage,
                assessment_date=datetime.now().strftime("%Y-%m-%d"),
                pest_risks=pest_risks,
                risk_timeline_7_days=[],
                preventive_measures=preventive_measures,
                weather_factors=[],
                recommendations=[],
                shap_explanation=shap_explanation,
                success=True,
                message="Pest risk assessment completed successfully"
            )
"""
# Replace the return statement in pest_service.py
old_return = """            return PestRiskResponse(
                crop=request.crop,
                location=f"{request.district or ''}, {request.state}".strip(", "),
                growth_stage=request.growth_stage,
                assessment_date=datetime.now().strftime("%Y-%m-%d"),
                pest_risks=pest_risks,
                risk_timeline_7_days=[],
                preventive_measures=preventive_measures,
                weather_factors=[],
                recommendations=[]
            )"""

content = content.replace(old_return, importances_code.strip())
with open("backend/app/services/pest_service.py", "w") as f:
    f.write(content)
