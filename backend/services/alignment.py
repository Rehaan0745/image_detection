import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alignment_engine")

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Applies noise reduction, grayscale conversion, and contrast enhancement
    using CLAHE for robust SIFT keypoint detection.
    """
    # 1. Grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 2. Bilateral Filter (removes noise while preserving sharp edges)
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(denoised)
    
    return equalized

def align_images(query_img: np.ndarray, ref_img: np.ndarray):
    """
    Aligns the query image to the reference image using SIFT and Homography.
    Returns:
        warped_query: Aligned version of query_img (same dimensions as ref_img)
        homography: The transformation matrix
        inliers_ratio: Quality metric (SIFT inliers / total matches)
        message: Status info
    """
    ref_h, ref_w = ref_img.shape[:2]
    
    # Preprocess
    query_gray = preprocess_image(query_img)
    ref_gray = preprocess_image(ref_img)
    
    # SIFT detector
    sift = cv2.SIFT_create(nfeatures=2000)
    kp_query, des_query = sift.detectAndCompute(query_gray, None)
    kp_ref, des_ref = sift.detectAndCompute(ref_gray, None)
    
    if des_query is None or des_ref is None:
        logger.warning("SIFT descriptors could not be computed.")
        return query_img, None, 0.0, "Could not extract image features. Check lighting/focus."
    
    # FLANN Matcher
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    try:
        matches = flann.knnMatch(des_query, des_ref, k=2)
    except Exception as e:
        logger.error(f"FLANN matching failed: {e}")
        return query_img, None, 0.0, f"Feature matching failed: {str(e)}"
    
    # Ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
            
    logger.info(f"Number of good SIFT matches: {len(good_matches)}")
    
    if len(good_matches) < 8:
        logger.warning("Too few good SIFT matches for reliable homography.")
        return query_img, None, 0.0, "Carton is not recognized or is too blurry. Alignment failed."
        
    src_pts = np.float32([kp_query[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # Homography
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    if H is None:
        logger.warning("Homography calculation failed.")
        return query_img, None, 0.0, "Failed to compute alignment homography mapping."
        
    # Quality assessment
    inliers = mask.ravel().tolist()
    num_inliers = sum(inliers)
    inliers_ratio = num_inliers / len(good_matches) if len(good_matches) > 0 else 0.0
    logger.info(f"SIFT RANSAC Inliers: {num_inliers} out of {len(good_matches)} ({inliers_ratio:.2%})")
    
    # Warp perspective
    warped_query = cv2.warpPerspective(query_img, H, (ref_w, ref_h))
    
    return warped_query, H, inliers_ratio, "Success"
