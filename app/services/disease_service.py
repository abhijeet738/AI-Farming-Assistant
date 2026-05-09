import io
import time
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import timm
from app.models.disease_detect import DiseaseDetectResponse, DiseasePrediction
from app.ml.model_registry import registry
import structlog

logger = structlog.get_logger()

# Define the exact architecture used in training
class PlantDiseaseModel(nn.Module):
    def __init__(self, num_classes, pretrained=False):
        super().__init__()
        
        self.backbone = timm.create_model(
            'tf_efficientnetv2_s',
            pretrained=pretrained,
            num_classes=0
        )
        
        self.feature_dim = self.backbone.num_features
        
        self.shared_fc = nn.Sequential(
            nn.Linear(self.feature_dim, 512),
            nn.LayerNorm(512),
            nn.ReLU(),
            nn.Dropout(0.3),
        )
        
        self.disease_head = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
        
        self.binary_head = nn.Sequential(
            nn.Linear(512, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        shared = self.shared_fc(features)
        disease_logits = self.disease_head(shared)
        binary_logits = self.binary_head(shared)
        return disease_logits, binary_logits, features


class DiseaseService:
    def __init__(self):
        # The registry returns the path to the model file for PyTorch
        self.model_path = registry.base_path / "disease_detection" / "best_model.pth"
        self.model = None
        self.idx_to_class = {}
        self.disease_kb = registry.get_kb("disease_rules") or {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        
        self.transform = transforms.Compose([
            transforms.Resize((384, 384)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()

    def _load_model(self):
        try:
            if not self.model_path.exists():
                logger.error("Disease vision model file not found", path=str(self.model_path))
                return

            logger.info("Loading PyTorch disease detection model...", device=str(self.device))
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            num_classes = checkpoint.get("num_classes", 117)
            self.idx_to_class = checkpoint.get("idx_to_class", {})
            
            # If idx_to_class missing, try to reverse class_to_idx
            if not self.idx_to_class and "class_to_idx" in checkpoint:
                self.idx_to_class = {v: k for k, v in checkpoint["class_to_idx"].items()}

            self.model = PlantDiseaseModel(num_classes=num_classes, pretrained=False)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.to(self.device)
            self.model.eval()
            logger.info("PyTorch model loaded successfully", num_classes=num_classes)
            
        except Exception as e:
            logger.error("Failed to load disease model", error=str(e))
            self.model = None

    def _get_disease_info(self, disease_label: str):
        """Fetch treatments and symptoms from knowledge base"""
        # Remove 'Crop___' prefix to search KB
        clean_name = disease_label.split("___")[-1].replace("_", " ").strip()
        crop_name = disease_label.split("___")[0].strip() if "___" in disease_label else ""
        
        # Search KB
        for key, rule in self.disease_kb.items():
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
        
        if self.model is None:
            return self._fallback_response()

        try:
            # Preprocess Image
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                disease_logits, binary_logits, _ = self.model(tensor)
                
                disease_probs = torch.softmax(disease_logits, dim=1)[0]
                binary_prob = torch.sigmoid(binary_logits)[0].item()
                
                # Get Top 3 predictions
                top_probs, top_indices = torch.topk(disease_probs, 3)
                
            predictions = []
            primary_crop = "Unknown"
            
            for i in range(3):
                idx = top_indices[i].item()
                prob = top_probs[i].item()
                
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
                    confidence=round(prob * 100, 1),
                    is_healthy=is_healthy_class,
                    symptoms=[] if is_healthy_class else kb_info["symptoms"],
                    treatment_recommendations=["No treatment needed"] if is_healthy_class else kb_info["treatments"]
                ))
            
            # Binary model confidence (0 = healthy, 1 = diseased)
            overall_health = 100.0 - (binary_prob * 100.0)

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
            message="PyTorch Vision model not loaded."
        )
