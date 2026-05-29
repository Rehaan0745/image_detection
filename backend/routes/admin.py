import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models_db as models
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DATASET_DIR = os.path.join(BACKEND_DIR, "static", "reference")
os.makedirs(REF_DATASET_DIR, exist_ok=True)

class MedicineCreate(BaseModel):
    name: str
    dosage: str | None = None
    manufacturer: str | None = None


from fastapi import Request, Response
import hashlib


def _expected_session_value():
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if not (ADMIN_EMAIL and ADMIN_PASSWORD):
        return None
    hv = hashlib.sha256(f"{ADMIN_EMAIL}:{ADMIN_PASSWORD}".encode('utf-8')).hexdigest()
    return hv


def require_admin(request: Request):
    """Require admin session cookie when ADMIN_EMAIL/ADMIN_PASSWORD env vars are set.
    Server sets an httponly cookie `admin_session` on successful login. If admin creds are not configured, allow access (dev convenience).
    """
    expected = _expected_session_value()
    if expected is None:
        return True
    cookie_val = request.cookies.get('admin_session')
    if not cookie_val or cookie_val != expected:
        raise HTTPException(status_code=401, detail="Admin login required")
    return True

@router.post('/login')
def admin_login(
    email: str = Form(...),
    password: str = Form(...),
    response: Response = None
):
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if not (ADMIN_EMAIL and ADMIN_PASSWORD):
        raise HTTPException(status_code=500, detail='Admin credentials not configured on server')
    if email != ADMIN_EMAIL or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail='Invalid admin credentials')
    session_value = hashlib.sha256(f"{ADMIN_EMAIL}:{ADMIN_PASSWORD}".encode('utf-8')).hexdigest()
    resp = Response()
    resp.set_cookie('admin_session', session_value, httponly=True, samesite='Lax')
    resp.status_code = 200
    return resp


@router.post('/logout')
def admin_logout(response: Response):
    response.delete_cookie('admin_session')
    return {"message": "logged out"}


@router.get('/session')
def check_session(request: Request):
    expected = _expected_session_value()
    if expected is None:
        return {"is_admin": True}
    cookie_val = request.cookies.get('admin_session')
    return {"is_admin": bool(cookie_val == expected)}

@router.get("/medicines")
def list_medicines(db: Session = Depends(get_db)):
    medicines = db.query(models.Medicine).all()
    result = []
    for med in medicines:
        views = []
        for view in med.views:
            views.append({
                "id": view.id,
                "view_name": view.view_name,
                "image_path": f"/static/reference/{med.name}/{os.path.basename(view.image_path)}"
            })
        result.append({
            "id": med.id,
            "name": med.name,
            "dosage": getattr(med, 'dosage', None),
            "created_at": med.created_at.isoformat(),
            "views": views
        })
    return result

@router.post("/medicines")
async def create_medicine(
    name: str = Form(...),
    dosage: str | None = Form(None),
    manufacturer: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin)
):
    # Check if exists
    existing = db.query(models.Medicine).filter(models.Medicine.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Medicine with this name already exists")
        
    db_med = models.Medicine(name=name, dosage=dosage, manufacturer=manufacturer)
    db.add(db_med)
    db.commit()
    db.refresh(db_med)
    
    # Create local directory
    med_dir = os.path.join(REF_DATASET_DIR, name)
    os.makedirs(med_dir, exist_ok=True)

    response = {"id": db_med.id, "name": db_med.name, "dosage": db_med.dosage, "manufacturer": db_med.manufacturer, "message": "Medicine created"}

    if file is not None:
        ext = os.path.splitext(file.filename)[1]
        if not ext.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="File format not supported. Upload an image (JPG/PNG).")

        filename = f"full_{int(datetime.utcnow().timestamp())}{ext}"
        dest_path = os.path.join(med_dir, filename)
        try:
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        ref_view = models.ReferenceView(
            medicine_id=db_med.id,
            view_name="full",
            image_path=dest_path
        )
        db.add(ref_view)
        db.commit()
        db.refresh(ref_view)

        response["view"] = {
            "id": ref_view.id,
            "view_name": ref_view.view_name,
            "image_path": f"/static/reference/{name}/{filename}"
        }

    return response

@router.post("/medicines/{medicine_id}/views")
async def upload_reference_view(
    medicine_id: int,
    view_name: str = Form(...),  # front, back, side, top, seal, barcode
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
    , _admin=Depends(require_admin)):
    medicine = db.query(models.Medicine).filter(models.Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
        
    # Allow 'full' as a valid upload type as we accept full-carton images now
    valid_views = ["front", "back", "side", "top", "seal", "barcode", "full"]
    if view_name not in valid_views:
        raise HTTPException(status_code=400, detail=f"Invalid view name. Must be one of {valid_views}")
        
    # Set up folders
    med_dir = os.path.join(REF_DATASET_DIR, medicine.name)
    os.makedirs(med_dir, exist_ok=True)
    
    # File save location
    ext = os.path.splitext(file.filename)[1]
    if not ext.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="File format not supported. Upload an image (JPG/PNG).")
        
    filename = f"{view_name}_{int(datetime.utcnow().timestamp())}{ext}"
    dest_path = os.path.join(med_dir, filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    # Save reference view entry
    ref_view = models.ReferenceView(
        medicine_id=medicine_id,
        view_name=view_name,
        image_path=dest_path
    )
    db.add(ref_view)
    db.commit()
    db.refresh(ref_view)
    
    return {
        "id": ref_view.id,
        "view_name": ref_view.view_name,
        "image_path": f"/static/reference/{medicine.name}/{filename}"
    }

@router.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    medicine = db.query(models.Medicine).filter(models.Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
        
    # Remove files
    med_dir = os.path.join(REF_DATASET_DIR, medicine.name)
    if os.path.exists(med_dir):
        try:
            shutil.rmtree(med_dir)
        except Exception as e:
            logger.error(f"Failed to remove directory {med_dir}: {e}")
            
    db.delete(medicine)
    db.commit()
    return {"message": f"Medicine and all views deleted successfully."}

@router.delete("/views/{view_id}")
def delete_view(view_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    view = db.query(models.ReferenceView).filter(models.ReferenceView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="Reference view not found")
        
    # Remove file
    if os.path.exists(view.image_path):
        try:
            os.remove(view.image_path)
        except Exception as e:
            logger.error(f"Failed to delete reference file {view.image_path}: {e}")
            
    db.delete(view)
    db.commit()
    return {"message": "View deleted successfully."}
