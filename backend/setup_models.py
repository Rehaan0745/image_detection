import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_models")

# Add backend dir to path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BACKEND_DIR)

WEIGHTS_DIR = os.path.join(BACKEND_DIR, "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Set environment variables for local caching
os.environ["TORCH_HOME"] = WEIGHTS_DIR
os.environ["EASYOCR_MODULE_PATH"] = WEIGHTS_DIR

def main():
    logger.info("Starting offline models pre-download...")
    
    # 1. Download PyTorch ResNet18 Weights
    logger.info("Step 1: Downloading PyTorch ResNet18 weights...")
    try:
        import torch
        import torchvision.models as models
        # This will download and save it to WEIGHTS_DIR/hub/checkpoints/
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        logger.info("ResNet18 weights successfully downloaded and cached.")
    except Exception as e:
        logger.error(f"Failed to download ResNet18 weights: {e}")
        
    # 2. Download EasyOCR Model weights (CRAFT detector + English recognizer)
    logger.info("Step 2: Downloading EasyOCR model weights...")
    try:
        import easyocr
        # Initializing the Reader with download_enabled=True will download the models to WEIGHTS_DIR/model/
        reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=WEIGHTS_DIR, download_enabled=True)
        logger.info("EasyOCR English models successfully downloaded and cached.")
    except Exception as e:
        logger.error(f"Failed to download EasyOCR models: {e}")
        
    logger.info("Offline models setup complete. Weights are cached locally.")

if __name__ == "__main__":
    main()
