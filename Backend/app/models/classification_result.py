# app/models/classification_result.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id              = Column(Integer, primary_key=True, index=True)
    ticket_id       = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    
    # ✅ Relation inverse
    ticket          = relationship("Ticket", back_populates="classifications")
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

    # ── V3.0 : XAI (SHAP) + NLP ──────────────────────────────────────────────
    shap_values   = Column(JSON,    nullable=True)  # {feature: shap_value} — vraie XAI
    nlp_score     = Column(Integer, nullable=True)  # 0-100 : qualité justification
    nlp_label     = Column(String(30), nullable=True)  # LEGIT/VAGUE/SUSPICIOUS/URGENT_SANS_MOTIF
    trust_modifier= Column(Integer, nullable=True)  # modificateur appliqué depuis trust_score