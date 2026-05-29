from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    dosage = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    views = relationship("ReferenceView", back_populates="medicine", cascade="all, delete-orphan")

class ReferenceView(Base):
    __tablename__ = "reference_views"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    view_name = Column(String, nullable=False)  # front, back, side, top, seal, barcode
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="views")
