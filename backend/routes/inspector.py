import os
import cv2
import numpy as np
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models_db as models
from ..services.alignment import align_images
from ..services.diff_detector import detect_visual_differences
from ..services.ocr_engine import OfflineOCREngine, compare_ocr_texts
from ..services.classifier import RegionalFeatureExtractor
from ..services.explanation import generate_semantic_explanations
from ..services.report import generate_pdf_report

router = APIRouter(prefix="/api/inspect", tags=["inspector"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERY_DIR = os.path.join(BACKEND_DIR, "static", "query")
REPORTS_DIR = os.path.join(BACKEND_DIR, "static", "reports")
os.makedirs(QUERY_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Initialize engines
ocr_engine = OfflineOCREngine()
feature_extractor = RegionalFeatureExtractor()

@router.post("/compare")
async def compare_carton(
    medicine_id: int = Form(...),
    view_name: str = Form('full'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Fetch reference packaging view
    ref_view = db.query(models.ReferenceView).filter(
        models.ReferenceView.medicine_id == medicine_id,
        models.ReferenceView.view_name == view_name
    ).first()
    
    if not ref_view:
        raise HTTPException(status_code=404, detail="No authentic reference image found for this view.")
        
    medicine = db.query(models.Medicine).filter(models.Medicine.id == medicine_id).first()
    
    # 2. Save query file temporarily
    ext = os.path.splitext(file.filename)[1]
    timestamp_str = str(int(datetime.utcnow().timestamp()))
    query_filename = f"query_{timestamp_str}{ext}"
    query_path = os.path.join(QUERY_DIR, query_filename)
    
    try:
        with open(query_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write query image file: {str(e)}")
        
    # 3. Load images
    query_img = cv2.imread(query_path)
    ref_img = cv2.imread(ref_view.image_path)
    
    if query_img is None or ref_img is None:
        raise HTTPException(status_code=400, detail="Failed to parse query or reference image.")
        
    # Keep copies of original shapes
    ref_h, ref_w = ref_img.shape[:2]
    
    # 4. Alignment
    warped_query, H, alignment_quality, align_msg = align_images(query_img, ref_img)
    
    # If alignment completely fails, return alignment failure metrics
    if H is None or alignment_quality < 0.05:
        return {
            "authenticity_score": 0.0,
            "risk_level": "high",
            "explanations": [{
                "category": "Alignment Engine",
                "severity": "critical",
                "text": f"Image alignment failed: {align_msg}. Please upload a clearer, straight image.",
                "box": [0, 0, ref_w, ref_h]
            }],
            "annotated_query_url": f"/static/query/{query_filename}",
            "reference_url": f"/static/reference/{medicine.name}/{os.path.basename(ref_view.image_path)}",
            "pdf_report_url": None
        }
        
    # 5. Visual & Color Difference Detection
    visual_diffs, ssim_score, annotated_warped = detect_visual_differences(warped_query, ref_img)
    
    # 6. OCR Text Extraction and Verification
    ref_ocr_regions = ocr_engine.get_text_regions(ref_img)
    query_ocr_regions = ocr_engine.get_text_regions(warped_query)
    ocr_diffs = compare_ocr_texts(query_ocr_regions, ref_ocr_regions)
    
    # 7. Deep Feature Similarity on differences (Siamese-like verify)
    # For any structural discrepancy, we crop and compare using deep learning feature representation
    deep_matches_passed = 0
    total_deep_matches = 0
    
    for diff in visual_diffs:
        x, y, w, h = diff["box"]
        # Ensure coordinates are within image boundaries
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(ref_w, x + w), min(ref_h, y + h)
        
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            ref_crop = ref_img[y1:y2, x1:x2]
            query_crop = warped_query[y1:y2, x1:x2]
            
            sim = feature_extractor.compare_regions(ref_crop, query_crop)
            diff["deep_similarity"] = sim
            total_deep_matches += 1
            if sim > 0.88:
                deep_matches_passed += 1
                
    # 8. Compute Semantic Explanations
    explanations = generate_semantic_explanations(visual_diffs, ocr_diffs, ref_w, ref_h)
    
    # 9. Compute Overall Authenticity Score
    # We combine multiple metrics:
    # - Alignment (20%): Key for correct structure
    # - SSIM (40%): Structural shape layout similarity
    # - Color LAB Distance (15%): Shade accuracy
    # - OCR Text Correctness (25%): Character level accuracy
    
    # Compute OCR text correctness ratio
    total_ref_texts = len(ref_ocr_regions)
    ocr_errors = len([d for d in ocr_diffs if d["type"] in ["text_mismatch", "missing_text"]])
    ocr_score = (1.0 - (ocr_errors / max(1, total_ref_texts))) * 100.0
    
    # Raw metrics
    raw_alignment = alignment_quality * 100.0
    raw_ssim = ssim_score * 100.0
    
    # Mean color similarity: Delta E mean across whole image
    # Simple proxy: 100 - (average Delta E)
    # A Delta E of 0 is perfect, 20 is significant difference
    lab_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2LAB)
    lab_warped = cv2.cvtColor(warped_query, cv2.COLOR_BGR2LAB)
    delta_e = np.sqrt(np.sum((lab_ref.astype("float32") - lab_warped.astype("float32")) ** 2, axis=2))
    mean_delta_e = np.mean(delta_e)
    color_score = max(0.0, min(100.0, 100.0 - (mean_delta_e * 2.0)))
    
    # Overall Score formula
    authenticity_score = (
        0.20 * raw_alignment +
        0.40 * raw_ssim +
        0.15 * color_score +
        0.25 * ocr_score
    )
    
    # Severity penalization
    has_critical = any(item["severity"] == "critical" for item in explanations)
    has_suspicious = any(item["severity"] == "suspicious" for item in explanations)
    
    if has_critical:
        # Heavily cap maximum score if there is a critical mismatch (like wrong batch, expiry, or missing brand logo)
        authenticity_score = min(72.0, authenticity_score)
        risk_level = "high"
    elif has_suspicious:
        authenticity_score = min(88.0, authenticity_score)
        risk_level = "medium"
    else:
        risk_level = "low" if authenticity_score >= 90.0 else "medium"
        
    # Cap between 0 and 100
    authenticity_score = max(0.0, min(100.0, authenticity_score))
    
    # 10. Save Annotated Warped image in static query folder to serve to client
    annotated_filename = f"annotated_{timestamp_str}.jpg"
    annotated_path = os.path.join(BACKEND_DIR, "static", "query", annotated_filename)
    os.makedirs(os.path.dirname(annotated_path), exist_ok=True)
    cv2.imwrite(annotated_path, annotated_warped)
    
    # Also save original warped query for side-by-side display without overlays if wanted
    warped_filename = f"warped_{timestamp_str}.jpg"
    warped_path = os.path.join(BACKEND_DIR, "static", "query", warped_filename)
    cv2.imwrite(warped_path, warped_query)
    
    # 11. Generate PDF Report
    pdf_filename = f"inspection_report_{timestamp_str}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    generate_pdf_report(
        output_path=pdf_path,
        medicine_name=medicine.name,
        view_name=view_name,
        authenticity_score=authenticity_score,
        risk_level=risk_level,
        explanations=explanations,
        timestamp=time_str
    )
    
    return {
        "authenticity_score": round(authenticity_score, 1),
        "risk_level": risk_level,
        "explanations": explanations,
        "annotated_query_url": f"/static/query/{annotated_filename}",
        "warped_query_url": f"/static/query/{warped_filename}",
        "reference_url": f"/static/reference/{medicine.name}/{os.path.basename(ref_view.image_path)}",
        "pdf_report_url": f"/static/reports/{pdf_filename}",
        "alignment_quality": round(alignment_quality * 100.0, 1),
        "ssim_score": round(ssim_score * 100.0, 1),
        "color_match": round(color_score, 1),
        "ocr_match": round(ocr_score, 1)
    }
