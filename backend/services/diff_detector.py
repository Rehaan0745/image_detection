import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diff_detector")

def detect_visual_differences(aligned_query: np.ndarray, reference: np.ndarray, ssim_threshold: float = 0.85, delta_e_threshold: float = 12.0):
    """
    Compares aligned query image and reference image.
    Detects structural and color differences.
    Returns:
        diff_regions: List of dicts, each with {box: [x,y,w,h], type: str, severity: str, score: float}
        ssim_score: Float, average SSIM
        annotated_image: Warped query image with highlighted difference rectangles
    """
    # 1. Structural Comparison (SSIM)
    gray_aligned = cv2.cvtColor(aligned_query, cv2.COLOR_BGR2GRAY)
    gray_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    
    # Bilateral blur before SSIM to ignore sub-pixel printing noise and focuses on structural elements
    gray_aligned_blur = cv2.bilateralFilter(gray_aligned, d=5, sigmaColor=35, sigmaSpace=35)
    gray_reference_blur = cv2.bilateralFilter(gray_reference, d=5, sigmaColor=35, sigmaSpace=35)
    
    score, diff_map = ssim(gray_reference_blur, gray_aligned_blur, full=True)
    
    # Scale diff_map to 0-255
    diff_map = (diff_map * 255).astype("uint8")
    
    # Threshold the diff map (low similarity is black/dark)
    _, ssim_thresh = cv2.threshold(diff_map, int(ssim_threshold * 255), 255, cv2.THRESH_BINARY_INV)
    
    # Clean noise with morphological opening
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    ssim_thresh = cv2.morphologyEx(ssim_thresh, cv2.MORPH_OPEN, kernel)
    ssim_thresh = cv2.morphologyEx(ssim_thresh, cv2.MORPH_CLOSE, kernel)
    
    # 2. Color Comparison (LAB Delta E proxy)
    lab_aligned = cv2.cvtColor(aligned_query, cv2.COLOR_BGR2LAB)
    lab_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2LAB)
    
    # Split channels
    l_ref, a_ref, b_ref = cv2.split(lab_reference)
    l_ali, a_ali, b_ali = cv2.split(lab_aligned)
    
    # Compute Euclidean distance in LAB space
    dist_l = (l_ref.astype("float32") - l_ali.astype("float32")) ** 2
    dist_a = (a_ref.astype("float32") - a_ali.astype("float32")) ** 2
    dist_b = (b_ref.astype("float32") - b_ali.astype("float32")) ** 2
    delta_e = np.sqrt(dist_l + dist_a + dist_b)
    
    # Create binary mask of color differences
    color_diff_mask = (delta_e > delta_e_threshold).astype("uint8") * 255
    color_diff_mask = cv2.morphologyEx(color_diff_mask, cv2.MORPH_OPEN, kernel)
    
    # 3. Combine masks and extract contours
    combined_mask = cv2.bitwise_or(ssim_thresh, color_diff_mask)
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    diff_regions = []
    annotated_image = aligned_query.copy()
    
    h_img, w_img = aligned_query.shape[:2]
    min_area = (h_img * w_img) * 0.0003  # ignore microscopic features
    
    for idx, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < min_area:
            continue
            
        # Determine difference type
        # Analyze local region color difference vs structural difference
        roi_delta_e = delta_e[y:y+h, x:x+w]
        mean_delta_e = np.mean(roi_delta_e)
        
        roi_ssim = diff_map[y:y+h, x:x+w]
        mean_ssim = np.mean(roi_ssim) / 255.0
        
        diff_type = "structural"
        if mean_delta_e > delta_e_threshold * 1.5 and mean_ssim > 0.8:
            diff_type = "color"
        elif mean_delta_e > delta_e_threshold * 1.2 and mean_ssim < 0.8:
            diff_type = "mixed"
            
        # Determine severity
        score_val = (1.0 - mean_ssim) * 100.0
        if score_val > 55.0 or area > (h_img * w_img) * 0.05:
            severity = "critical"
            color = (0, 0, 255)  # Red
        elif score_val > 30.0 or area > (h_img * w_img) * 0.01:
            severity = "suspicious"
            color = (0, 165, 255)  # Orange
        else:
            severity = "minor"
            color = (0, 255, 255)  # Yellow
            
        diff_regions.append({
            "id": idx,
            "box": [x, y, w, h],
            "type": diff_type,
            "severity": severity,
            "score": float(score_val),
            "mean_delta_e": float(mean_delta_e)
        })
        
        # Draw bounding boxes and labels
        cv2.rectangle(annotated_image, (x, y), (x + w, y + h), color, 2)
        # Put small text label
        cv2.putText(annotated_image, f"Diff #{idx} ({severity})", (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
                    
    return diff_regions, float(score), annotated_image
