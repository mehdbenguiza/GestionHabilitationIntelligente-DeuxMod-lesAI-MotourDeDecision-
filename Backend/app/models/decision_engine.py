# app/models/decision_engine.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base

class DecisionEngine(Base):
    __tablename__ = "decision_engine"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    classification_id = Column(Integer, ForeignKey("classification_results.id"), nullable=True)
    final_level = Column(String(20), nullable=False)
    final_confidence = Column(Float, nullable=False)
    recommended_action = Column(String(50), nullable=False)
    action_reason = Column(Text, nullable=True)
    rules_applied = Column(JSON, nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())