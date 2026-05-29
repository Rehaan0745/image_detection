import os
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("classifier_engine")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DIR = os.path.join(BACKEND_DIR, "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# Set torch hub dir to our offline weights directory
os.environ["TORCH_HOME"] = WEIGHTS_DIR

class RegionalFeatureExtractor:
    def __init__(self):
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
    def initialize_model(self):
        if self.model is None:
            try:
                # Load ResNet18. If internet is available during setup, it will be downloaded.
                # If offline, it reads from the cached directory.
                resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
                # Remove classification head to get features
                self.model = nn.Sequential(*list(resnet.children())[:-1])
                self.model.eval()
                logger.info("ResNet18 feature extractor initialized offline successfully.")
            except Exception as e:
                logger.error(f"Failed to load ResNet18 offline: {e}. Fallback to uninitialized weights.")
                # If offline loading fails, initialize model with random weights
                resnet = models.resnet18(weights=None)
                self.model = nn.Sequential(*list(resnet.children())[:-1])
                self.model.eval()

    def extract_features(self, image_np: np.ndarray) -> np.ndarray:
        """
        Extracts deep features from a numpy image patch.
        """
        self.initialize_model()
        if self.model is None:
            return np.zeros((512,))
            
        try:
            # Convert BGR (OpenCV) to RGB
            if len(image_np.shape) == 3:
                image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
                
            pil_img = Image.fromarray(image_rgb)
            tensor_img = self.transform(pil_img).unsqueeze(0)
            
            with torch.no_grad():
                features = self.model(tensor_img)
                # Flatten to vector
                features = torch.squeeze(features).numpy()
                
            # Normalize vector
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            return features
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.zeros((512,))

    def compare_regions(self, img1_crop: np.ndarray, img2_crop: np.ndarray) -> float:
        """
        Extracts features from both crops and returns their cosine similarity.
        """
        feat1 = self.extract_features(img1_crop)
        feat2 = self.extract_features(img2_crop)
        
        if np.all(feat1 == 0) or np.all(feat2 == 0):
            return 0.0
            
        similarity = np.dot(feat1, feat2)
        return float(similarity)
