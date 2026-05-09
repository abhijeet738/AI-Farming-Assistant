import os
import json
import joblib
import structlog
from pathlib import Path
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class ModelRegistry:
    """
    Singleton registry for loading and serving machine learning models.
    Loads models lazily on first request or explicitly at startup.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.base_path = Path(os.getenv("MODELS_PATH", "./ml_models"))
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.knowledge_bases: Dict[str, Any] = {}
        
        self._initialized = True
        logger.info("ModelRegistry initialized", base_path=str(self.base_path))

    def _load_joblib(self, file_path: Path) -> Optional[Any]:
        if file_path.exists():
            try:
                return joblib.load(file_path)
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}", error=str(e))
        else:
            logger.warning(f"File not found: {file_path}")
        return None

    def _load_json(self, file_path: Path) -> Optional[Dict]:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {file_path.name}", error=str(e))
        else:
            logger.warning(f"File not found: {file_path}")
        return None

    # --- Crop Recommendation ---
    def load_crop_models(self):
        logger.info("Loading Crop Recommendation models...")
        model_dir = self.base_path / "crop_recommendation"
        
        self.models["crop"] = self._load_joblib(model_dir / "stacking_ensemble_model.pkl")
        if not self.models["crop"]:
            self.models["crop"] = self._load_joblib(model_dir / "xgboost_model.pkl")
            
        self.scalers["crop"] = self._load_joblib(model_dir / "standard_scaler.pkl")
        self.encoders["crop"] = self._load_joblib(model_dir / "label_encoder.pkl")
        self.metadata["crop"] = self._load_json(model_dir / "model_metadata.json")
        return self.models["crop"] is not None

    # --- Yield Prediction ---
    def load_yield_models(self):
        logger.info("Loading Yield Prediction models...")
        model_dir = self.base_path / "yield_prediction"
        
        self.models["yield"] = self._load_joblib(model_dir / "stacking_meta_learner.pkl")
        if not self.models["yield"]:
            self.models["yield"] = self._load_joblib(model_dir / "xgboost_yield_model.pkl")
            
        self.scalers["yield"] = self._load_joblib(model_dir / "yield_scaler.pkl")
        self.encoders["yield"] = self._load_joblib(model_dir / "yield_encoders.pkl")
        self.metadata["yield"] = self._load_json(model_dir / "yield_model_metadata.json")
        return self.models["yield"] is not None

    # --- Market Price ---
    def load_market_models(self):
        logger.info("Loading Market Price models...")
        model_dir = self.base_path / "market_price"
        
        self.models["market"] = self._load_joblib(model_dir / "market_meta_model.pkl")
        if not self.models["market"]:
            self.models["market"] = self._load_joblib(model_dir / "market_xgb_model.pkl")
            
        self.scalers["market"] = self._load_joblib(model_dir / "market_scaler.pkl")
        self.encoders["market"] = self._load_joblib(model_dir / "market_encoders.pkl")
        self.metadata["market"] = self._load_json(model_dir / "market_model_metadata.json")
        return self.models["market"] is not None

    # --- Fertilizer Prediction ---
    def load_fertilizer_models(self):
        logger.info("Loading Fertilizer models...")
        model_dir = self.base_path / "fertilizer"
        
        self.models["fertilizer"] = self._load_joblib(model_dir / "fertilizer_xgb_model.pkl")
        self.scalers["fertilizer"] = self._load_joblib(model_dir / "fertilizer_scaler.pkl")
        self.encoders["fertilizer"] = self._load_joblib(model_dir / "fertilizer_encoders.pkl")
        self.metadata["fertilizer"] = self._load_json(model_dir / "fertilizer_model_metadata.json")
        
        # Additional knowledge bases
        self.knowledge_bases["fert_products"] = self._load_json(model_dir / "fertilizer_products.json")
        self.knowledge_bases["crop_npk"] = self._load_json(model_dir / "crop_npk_requirements.json")
        return self.models["fertilizer"] is not None

    # --- Pest & Disease Risk ---
    def load_pest_models(self):
        logger.info("Loading Pest Risk models...")
        model_dir = self.base_path / "pest_risk"
        
        self.models["pest_clf"] = self._load_joblib(model_dir / "pest_risk_xgb_model.pkl")
        self.models["pest_reg"] = self._load_joblib(model_dir / "pest_risk_regressor.pkl")
        self.scalers["pest"] = self._load_joblib(model_dir / "pest_risk_scaler.pkl")
        self.encoders["pest"] = self._load_joblib(model_dir / "pest_risk_encoders.pkl")
        self.metadata["pest"] = self._load_json(model_dir / "pest_risk_metadata.json")
        self.knowledge_bases["disease_rules"] = self._load_json(model_dir / "disease_knowledge_base.json")
        
        return self.models["pest_clf"] is not None and self.models["pest_reg"] is not None

    # --- Disease Image Detection ---
    def load_disease_detection_model(self):
        # NOTE: PyTorch models should ideally be loaded in their specific service 
        # to avoid making PyTorch a hard dependency for the entire backend if not needed.
        # We just verify it exists here.
        model_dir = self.base_path / "disease_detection"
        model_path = model_dir / "best_model.pth"
        if model_path.exists():
            self.metadata["disease_vision"] = {"path": str(model_path), "status": "available"}
            return True
        return False

    def load_all(self):
        """Load all models. Useful for startup events."""
        results = {
            "crop": self.load_crop_models(),
            "yield": self.load_yield_models(),
            "market": self.load_market_models(),
            "fertilizer": self.load_fertilizer_models(),
            "pest": self.load_pest_models(),
            "disease_vision": self.load_disease_detection_model()
        }
        logger.info("Model loading complete", status=results)
        return results

    # Getters
    def get_model(self, module: str, sub_model: str = None) -> Any:
        key = f"{module}_{sub_model}" if sub_model else module
        return self.models.get(key)
        
    def get_scaler(self, module: str) -> Any:
        return self.scalers.get(module)
        
    def get_encoders(self, module: str) -> Any:
        return self.encoders.get(module)
        
    def get_metadata(self, module: str) -> Dict:
        return self.metadata.get(module, {})
        
    def get_kb(self, kb_name: str) -> Dict:
        return self.knowledge_bases.get(kb_name, {})

registry = ModelRegistry()
