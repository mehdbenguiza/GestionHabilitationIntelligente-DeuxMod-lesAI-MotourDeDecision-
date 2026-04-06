# app/models/classification_result.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ClassificationResult(Base):
    __tablename__ = "classification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    predicted_level = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())