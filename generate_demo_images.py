import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from database import SessionLocal, engine, Base
import models_db as models

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(BACKEND_DIR, "static", "reference", "Paracetamol_500")
QUERY_DIR = os.path.join(BACKEND_DIR, "static", "query")

os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(QUERY_DIR, exist_ok=True)

def create_base_carton(is_authentic=True):
    # Create 800x600 canvas (light gray border representing package outline)
    img = Image.new('RGB', (800, 600), color='#F8FAFC')
    draw = ImageDraw.Draw(img)
    
    # Draw packaging border
    draw.rectangle([10, 10, 790, 590], outline='#CBD5E0', width=4)
    
    # 1. Draw top brand band
    # Authentic uses tech blue (#2563EB). Altered uses navy blue (#1E3A8A).
    band_color = '#2563EB' if is_authentic else '#1E3A8A'
    draw.rectangle([14, 14, 786, 120], fill=band_color)
    
    # 2. Draw brand logo (circle with cross symbol inside)
    # Authentic: logo centered at x=100. Altered: logo shifted left at x=70.
    logo_center_x = 100 if is_authentic else 60
    logo_color = '#10B981' if is_authentic else '#059669' # Slight color shift
    draw.ellipse([logo_center_x - 30, 67 - 30, logo_center_x + 30, 67 + 30], fill=logo_color)
    
    # Cross inside logo
    draw.rectangle([logo_center_x - 5, 67 - 20, logo_center_x + 5, 67 + 20], fill='#FFFFFF')
    draw.rectangle([logo_center_x - 20, 67 - 5, logo_center_x + 20, 67 + 5], fill='#FFFFFF')
    
    # 3. Text
    # For font, since we are offline and default font is simple, we will use default pillow font
    # but draw it cleanly
    try:
        font = ImageFont.load_default()
    except:
        font = None
        
    # Standard text draw utility (since load_default doesn't support custom size, we draw with scale or lines)
    # We will use large letters by drawing lines/boxes for a bold logo feel,
    # or just use default text drawing.
    # To draw large text with default font, we can draw a grid of pixels or just use standard text.
    # Standard text is fine.
    
    # Brand Text
    draw.text((180, 50), "PHARMA CARE LABS", fill="#FFFFFF")
    
    # Main Drug Title
    draw.text((100, 200), "Paracetamol Tablets IP", fill="#0F172A")
    draw.text((100, 240), "Strength: 500 mg", fill="#475569")
    
    # 4. Packaging seal area
    if is_authentic:
        # Silver/green authenticity seal strip at upper right flap
        draw.rectangle([680, 150, 770, 180], fill='#A7F3D0', outline='#059669', width=2)
        draw.text((690, 158), "ORIGINAL", fill='#065F46')
    else:
        # Counterfeit has missing seal! Or altered seal text
        # We leave it blank to trigger "Structural discrepancy: missing seal flap"
        pass
        
    # 5. Regulatory text & batch info
    # Exp Date: Authentic = 05/2029. Altered = 05/2030 (mismatch)
    exp_date = "EXP: 05/2029" if is_authentic else "EXP: 05/2030"
    # Batch code: Authentic = PAR-102. Altered = PAR-102 (same, but let's make font spacing different)
    batch_text = "BATCH NO: PAR-102"
    
    draw.text((100, 400), "MFG DATE: 05/2026", fill="#1E293B")
    draw.text((100, 430), exp_date, fill="#1E293B")
    draw.text((100, 460), batch_text, fill="#1E293B")
    draw.text((100, 490), "MAX RETAIL PRICE RS. 42.00", fill="#1E293B")
    
    # 6. QR Code visual block in lower right
    # Authentic: 120x120 QR. Altered: 90x90 QR (resized barcode/QR)
    qr_size = 120 if is_authentic else 90
    qr_x1, qr_y1 = 630, 430
    if not is_authentic:
        qr_x1 = 660  # Shifted due to smaller size
        qr_y1 = 460
        
    draw.rectangle([qr_x1, qr_y1, qr_x1 + qr_size, qr_y1 + qr_size], fill="#111827")
    
    # Draw simple grid pattern on QR code
    for i in range(qr_x1 + 10, qr_x1 + qr_size - 10, 15):
        for j in range(qr_y1 + 10, qr_y1 + qr_size - 10, 15):
            if (i+j) % 2 == 0:
                draw.rectangle([i, j, i+8, j+8], fill="#FFFFFF")
                
    return img

def main():
    print("Generating demo packaging images...")
    
    # Generate images
    ref_img = create_base_carton(is_authentic=True)
    query_img = create_base_carton(is_authentic=False)
    
    # Save reference
    ref_path = os.path.join(REF_DIR, "front_1.jpg")
    ref_img.save(ref_path)
    print(f"Saved authentic reference to: {ref_path}")
    
    # Save query
    query_path = os.path.join(QUERY_DIR, "demo_altered_carton.jpg")
    # Add slight rotation to query image to test alignment homography!
    # Rotating by 3 degrees makes SIFT + Homography warping highly visible and functional!
    query_rotated = query_img.rotate(3, resample=Image.BICUBIC, expand=True)
    query_rotated.save(query_path)
    print(f"Saved rotated/altered query to: {query_path}")
    
    # Seed Database
    print("Seeding SQLite database with demo product...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Remove existing medicine with name Paracetamol_500 if exists
    existing = db.query(models.Medicine).filter(models.Medicine.name == "Paracetamol_500").first()
    if existing:
        db.delete(existing)
        db.commit()
        
    med = models.Medicine(name="Paracetamol_500")
    db.add(med)
    db.commit()
    db.refresh(med)
    
    view = models.ReferenceView(
        medicine_id=med.id,
        view_name="front",
        image_path=ref_path
    )
    db.add(view)
    db.commit()
    
    db.close()
    print("Database seeded with 'Paracetamol_500' and reference views.")

if __name__ == "__main__":
    main()
