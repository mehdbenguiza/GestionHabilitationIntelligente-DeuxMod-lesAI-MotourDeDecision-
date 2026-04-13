# app/models/classification_result.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id              = Column(Integer, primary_key=True, index=True)
    ticket_id       = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    predicted_level = Column(String(20), nullable=False)
    confidence      = Column(Float, nullable=False)
    probabilities   = Column(JSON, nullable=True)
    model_version   = Column(String(50), nullable=True)
    processed_at    = Column(DateTime(timezone=True), server_default=func.now())

    # ── Explainability & Audit (Hybride) ────────────────────────────────────
    explanation   = Column(Text, nullable=True)   # Phrase lisible : "Pourquoi CRITICAL ?"
    risk_factors  = Column(JSON, nullable=True)   # Dict technique
    source        = Column(String(30), nullable=True, default="model")
    
    # Nouveaux champs pour Audit Gold (Phase Hybride)
    risk_score_rules        = Column(Integer, nullable=True)
    decision_source         = Column(String(50), nullable=True, default="HYBRID (ML + RULES)")
    consistency_status      = Column(String(20), nullable=True) # OK / WARNING
    consistency_message     = Column(Text, nullable=True)
    triggered_rules         = Column(JSON, nullable=True) # Liste de strings pour audit
    recommended_action      = Column(String(50), nullable=True) # AUTO_APPROVE / MANUAL_REVIEW / BLOCK
    confidence_level_label  = Column(String(50), nullable=True) # Fiable, Risqué, etc.
    # "model" | "human_correction" | "fallback" | "error"