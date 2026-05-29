import os
import cv2
import numpy as np
import easyocr
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocr_engine")

# Define paths for weights
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DIR = os.path.join(BACKEND_DIR, "models", "weights")
os.makedirs(WEIGHTS_DIR, exist_ok=True)

class OfflineOCREngine:
    def __init__(self):
        self.reader = None
        
    def initialize_reader(self):
        if self.reader is None:
            try:
                # We enforce loading from WEIGHTS_DIR and do not allow runtime downloads
                self.reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=WEIGHTS_DIR, download_enabled=False)
                logger.info("EasyOCR initialized successfully offline.")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR offline: {e}. Attempting with download enabled as fallback.")
                try:
                    self.reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=WEIGHTS_DIR, download_enabled=True)
                except Exception as ex:
                    logger.error(f"EasyOCR fallback initialization failed: {ex}")
                    self.reader = None

    def get_text_regions(self, image: np.ndarray):
        """
        Executes OCR on an image.
        Returns a list of dicts: {"box": [x,y,w,h], "text": str, "conf": float}
        """
        self.initialize_reader()
        if self.reader is None:
            return []
            
        try:
            results = self.reader.readtext(image)
            text_regions = []
            for bbox, text, conf in results:
                # bbox is list of 4 points: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                xs = [pt[0] for pt in bbox]
                ys = [pt[1] for pt in bbox]
                x1, y1 = int(min(xs)), int(min(ys))
                x2, y2 = int(max(xs)), int(max(ys))
                w = x2 - x1
                h = y2 - y1
                
                text_regions.append({
                    "box": [x1, y1, w, h],
                    "text": text.strip(),
                    "conf": float(conf)
                })
            return text_regions
        except Exception as e:
            logger.error(f"OCR reading failed: {e}")
            return []

def calculate_iou(box1, box2):
    """
    Computes Intersection over Union (IoU) of two bounding boxes.
    Format: [x, y, w, h]
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    # Coordinates of intersection rectangle
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
        
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = w1 * h1
    box2_area = w2 * h2
    
    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou

def compare_ocr_texts(query_regions, ref_regions, text_diff_threshold=0.8):
    """
    Compares query and reference OCR regions.
    Identifies mismatching, missing, or layout-altered texts.
    """
    differences = []
    matched_query_indices = set()
    
    for r_idx, ref_reg in enumerate(ref_regions):
        ref_box = ref_reg["box"]
        ref_text = ref_reg["text"]
        
        # Try to find corresponding region in query (highest IoU or closest center)
        best_query_idx = -1
        best_iou = 0.0
        
        for q_idx, query_reg in enumerate(query_regions):
            if q_idx in matched_query_indices:
                continue
            iou = calculate_iou(ref_box, query_reg["box"])
            if iou > best_iou:
                best_iou = iou
                best_query_idx = q_idx
                
        # If we found a matching region (IoU > 0.15)
        if best_query_idx != -1 and best_iou > 0.15:
            matched_query_indices.add(best_query_idx)
            query_reg = query_regions[best_query_idx]
            query_text = query_reg["text"]
            query_box = query_reg["box"]
            
            # 1. Compare text values
            if ref_text.lower() != query_text.lower():
                # Text mismatch
                differences.append({
                    "type": "text_mismatch",
                    "severity": "critical" if any(k in ref_text.lower() for k in ["exp", "batch", "mfg", "mrp", "rs", "strength", "mg"]) else "suspicious",
                    "ref_text": ref_text,
                    "query_text": query_text,
                    "box": query_box,
                    "ref_box": ref_box,
                    "reason": f"Text value mismatch. Expected '{ref_text}', got '{query_text}'"
                })
            else:
                # Same text, check layout differences (font size, spacing)
                # Font size is estimated by bounding box height
                h_diff_ratio = abs(ref_box[3] - query_box[3]) / float(ref_box[3])
                # Spacing/Width difference ratio
                w_diff_ratio = abs(ref_box[2] - query_box[2]) / float(ref_box[2])
                
                if h_diff_ratio > 0.25:
                    differences.append({
                        "type": "font_size_mismatch",
                        "severity": "minor",
                        "ref_text": ref_text,
                        "query_text": query_text,
                        "box": query_box,
                        "ref_box": ref_box,
                        "reason": f"Font size differs for text '{ref_text}'. Expected height {ref_box[3]}px, got {query_box[3]}px"
                    })
                elif w_diff_ratio > 0.3:
                    differences.append({
                        "type": "text_spacing_mismatch",
                        "severity": "minor",
                        "ref_text": ref_text,
                        "query_text": query_text,
                        "box": query_box,
                        "ref_box": ref_box,
                        "reason": f"Text character spacing/width differs for '{ref_text}'"
                    })
        else:
            # Text is present in reference but missing in query
            differences.append({
                "type": "missing_text",
                "severity": "critical" if any(k in ref_text.lower() for k in ["exp", "batch", "mfg", "mrp", "rs", "strength", "mg"]) else "suspicious",
                "ref_text": ref_text,
                "query_text": "",
                "box": ref_box,
                "ref_box": ref_box,
                "reason": f"Required text '{ref_text}' is missing from the query carton"
            })
            
    # Check for unexpected text added to the query carton
    for q_idx, query_reg in enumerate(query_regions):
        if q_idx not in matched_query_indices:
            differences.append({
                "type": "unexpected_text",
                "severity": "suspicious",
                "ref_text": "",
                "query_text": query_reg["text"],
                "box": query_reg["box"],
                "ref_box": None,
                "reason": f"Unexpected text '{query_reg['text']}' detected on query packaging"
            })
            
    return differences
