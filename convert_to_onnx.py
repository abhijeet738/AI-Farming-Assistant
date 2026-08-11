import os
import torch
import torch.onnx
import structlog
from pathlib import Path

# Important: We must import the model definition from where it currently lives
from app.services.disease_service import PlantDiseaseModel
from app.ml.model_registry import registry

logger = structlog.get_logger()

def convert_model():
    """Converts the PyTorch disease detection model to ONNX format."""
    logger.info("Starting ONNX conversion process...")

    # 1. Define paths
    model_dir = registry.base_path / "disease_detection"
    pth_path = model_dir / "best_model.pth"
    onnx_path = model_dir / "best_model.onnx"

    if not pth_path.exists():
        logger.error(f"PyTorch model not found at {pth_path}")
        return

    # 2. Load the PyTorch checkpoint
    logger.info("Loading PyTorch checkpoint...", path=str(pth_path))
    checkpoint = torch.load(pth_path, map_location="cpu", weights_only=False)
    num_classes = checkpoint.get("num_classes", 117)
    
    # Extract class mappings
    idx_to_class = checkpoint.get("idx_to_class", {})
    if not idx_to_class and "class_to_idx" in checkpoint:
        idx_to_class = {v: k for k, v in checkpoint["class_to_idx"].items()}

    # 3. Instantiate the PyTorch model and load weights
    logger.info("Instantiating PlantDiseaseModel...", num_classes=num_classes)
    model = PlantDiseaseModel(num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()  # MUST set to eval mode for inference/export

    # 4. Create a dummy input tensor (Batch Size 1, 3 Channels, 384x384 Image)
    # This is required by ONNX to trace the mathematical operations in the network.
    logger.info("Creating dummy input tensor...")
    dummy_input = torch.randn(1, 3, 384, 384)

    # 5. Export to ONNX
    logger.info("Exporting to ONNX format. This may take a minute...", output_path=str(onnx_path))
    torch.onnx.export(
        model,                      # The loaded PyTorch model
        dummy_input,                # The dummy input tensor
        str(onnx_path),             # Where to save the file
        export_params=True,         # Store the trained parameter weights inside the model file
        opset_version=17,           # ONNX opset version (17 is stable and modern)
        do_constant_folding=True,   # Optimize constant math operations
        input_names=['image'],      # Give the input a human-readable name
        output_names=['disease_logits', 'binary_logits', 'features'], # Name the outputs
        dynamic_axes={              # Allow the batch size to be dynamic (e.g. processing 5 images at once)
            'image': {0: 'batch_size'},
            'disease_logits': {0: 'batch_size'},
            'binary_logits': {0: 'batch_size'},
            'features': {0: 'batch_size'}
        }
    )

    logger.info("✅ Model successfully exported to ONNX!")
    
    # 6. Compare file sizes
    pth_size = os.path.getsize(pth_path) / (1024 * 1024)
    onnx_size = os.path.getsize(onnx_path) / (1024 * 1024)
    logger.info(f"Size comparison:", PyTorch=f"{pth_size:.1f} MB", ONNX=f"{onnx_size:.1f} MB")
    
    # 7. Save the class mapping for the ONNX runtime to use later
    # We will save it alongside the ONNX file since we won't be using the .pth file anymore
    import json
    mapping_path = model_dir / "class_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(idx_to_class, f, indent=4)
    logger.info("Class mapping saved", path=str(mapping_path))

if __name__ == "__main__":
    convert_model()
