import io
import time
import json

import numpy as np
import onnxruntime as ort
import structlog
from PIL import Image

from app.ml.model_registry import registry
from app.models.disease_detect import DiseaseDetectResponse, DiseasePrediction

logger = structlog.get_logger()

class DiseaseService:
    def __init__(self):
        # The registry returns the path to the model file
        self.model_path = registry.base_path / "disease_detection" / "best_model.onnx"
        self.mapping_path = registry.base_path / "disease_detection" / "class_mapping.json"
        
        self.session = None
        self.idx_to_class = {}
        self.disease_kb = registry.get_kb("disease_rules") or {}
        
        self._load_model()

    def _load_model(self):
        try:
            if not self.model_path.exists():
                logger.error("Disease ONNX model file not found", path=str(self.model_path))
                return

            logger.info("Loading ONNX disease detection model...")
            
            # Load ONNX Runtime Session (CPU by default)
            self.session = ort.InferenceSession(
                str(self.model_path), 
                providers=["CPUExecutionProvider"]
            )
            
            # Load class mappings
            if self.mapping_path.exists():
                with open(self.mapping_path, "r") as f:
                    raw_mapping = json.load(f)
                    # JSON keys are always strings, convert back to int
                    self.idx_to_class = {int(k): v for k, v in raw_mapping.items()}
                logger.info("ONNX model and class mapping loaded successfully", num_classes=len(self.idx_to_class))
            else:
                logger.warning("class_mapping.json not found. Disease labels will be unknown.")

        except Exception as e:
            logger.error("Failed to load disease ONNX model", error=str(e))
            self.session = None

    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Manually preprocess image to match PyTorch torchvision.transforms"""
        # Open and convert to RGB
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Resize to 384x384 (EfficientNetV2-S target size)
        img = img.resize((384, 384), Image.BILINEAR)
        
        # Convert to numpy array and scale to [0, 1]
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Normalize with ImageNet mean and std
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_array = (img_array - mean) / std
        
        # PyTorch expects channels first (C, H, W) instead of (H, W, C)
        img_array = np.transpose(img_array, (2, 0, 1))
        
        # Add batch dimension (1, C, H, W)
        return np.expand_dims(img_array, axis=0)

    def _softmax(self, x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=1, keepdims=True)

    def _sigmoid(self, x):
        """Compute sigmoid."""
        return 1 / (1 + np.exp(-x))

    def _get_disease_info(self, disease_label: str):
        """Fetch treatments and symptoms from knowledge base"""
        # Remove 'Crop___' prefix to search KB
        clean_name = disease_label.split("___")[-1].replace("_", " ").strip()
        crop_name = disease_label.split("___")[0].strip() if "___" in disease_label else ""

        # Search KB
        for _key, rule in self.disease_kb.items():
            if rule.get("disease", "").lower() == clean_name.lower():
                # Check if it's the right crop
                if crop_name and rule.get("crop", "").lower() != crop_name.lower():
                    continue

                treatments = rule.get("treatments", {})
                all_treatments = treatments.get("chemical", []) + treatments.get("organic", [])

                return {
                    "symptoms": rule.get("symptoms", ["Visible lesions or discoloration on leaves"]),
                    "treatments": all_treatments[:5]
                }

        return {
            "symptoms": ["Leaf discoloration", "Abnormal growth patterns"],
            "treatments": ["Remove infected leaves", "Consult local agricultural extension"]
        }

    async def detect_disease(self, image_bytes: bytes) -> DiseaseDetectResponse:
        start_time = time.time()

        if self.session is None:
            return self._fallback_response()

        try:
            # Preprocess Image
            tensor = self._preprocess_image(image_bytes)

            # ONNX Inference
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: tensor})
            
            # Unpack outputs (disease_logits, binary_logits, features)
            disease_logits = outputs[0]
            binary_logits = outputs[1]

            # Convert logits to probabilities
            disease_probs = self._softmax(disease_logits)[0]
            binary_prob = self._sigmoid(binary_logits)[0][0]

            # Get Top 3 predictions
            top_indices = np.argsort(disease_probs)[-3:][::-1]

            predictions = []
            primary_crop = "Unknown"

            for i, idx in enumerate(top_indices):
                prob = disease_probs[idx]

                # Filter out low confidence
                if prob < 0.05 and i > 0:
                    continue

                class_name = self.idx_to_class.get(idx, f"Class_{idx}")
                if i == 0 and "___" in class_name:
                    primary_crop = class_name.split("___")[0].replace("_", " ")

                is_healthy_class = "healthy" in class_name.lower()

                kb_info = self._get_disease_info(class_name)

                predictions.append(DiseasePrediction(
                    disease_name=class_name.replace("___", " ").replace("_", " "),
                    confidence=round(float(prob) * 100, 1),
                    is_healthy=is_healthy_class,
                    symptoms=[] if is_healthy_class else kb_info["symptoms"],
                    treatment_recommendations=["No treatment needed"] if is_healthy_class else kb_info["treatments"]
                ))

            # Binary model confidence (0 = healthy, 1 = diseased)
            overall_health = 100.0 - (float(binary_prob) * 100.0)

            analysis_time = (time.time() - start_time) * 1000

            return DiseaseDetectResponse(
                crop=primary_crop,
                predictions=predictions,
                is_plant=True,
                overall_health_score=round(overall_health, 1),
                analysis_time_ms=round(analysis_time, 2)
            )

        except Exception as e:
            logger.error("Disease detection failed", error=str(e))
            return self._fallback_response()

    def _fallback_response(self) -> DiseaseDetectResponse:
        return DiseaseDetectResponse(
            crop="Unknown",
            predictions=[DiseasePrediction(
                disease_name="System Unavailable",
                confidence=0.0,
                is_healthy=False,
                symptoms=[],
                treatment_recommendations=[]
            )],
            is_plant=False,
            overall_health_score=0.0,
            analysis_time_ms=0.0,
            success=False,
            message="ONNX Vision model not loaded."
        )
