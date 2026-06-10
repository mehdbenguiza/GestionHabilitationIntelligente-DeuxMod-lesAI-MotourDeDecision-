# app/models/anomaly_log.py
"""
Modèle SQLAlchemy — Table anomaly_logs
=======================================
Stocke le résultat de chaque analyse d'anomalie comportementale (Modèle 2).
Un enregistrement est créé pour chaque ticket analysé (sauf ADMIN_SIMULATION).
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id              = Column(Integer, primary_key=True, index=True)
    ticket_id       = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id     = Column(String(50), nullable=True, index=True)

    # ── Résultat Isolation Forest ────────────────────────────────────────────
    # Score entre -1.0 (très anormal) et +1.0 (très normal)
    # Valeur None si l'IF n'a pas pu être chargé (fallback sur règles seules)
    anomaly_score   = Column(Float, nullable=True)

    # ── Relations ────────────────────────────────────────────────────────────
    ticket          = relationship("Ticket", back_populates="anomaly_logs")

    # ── Verdict global ───────────────────────────────────────────────────────
    is_anomalous    = Column(Boolean, default=False, nullable=False)

    # ── Flags déclenchés (liste de strings) ─────────────────────────────────
    # Ex: ["ANOMALY_OUT_OF_HOURS", "ANOMALY_WEEKEND_SUBMISSION"]
    anomaly_flags   = Column(JSON, nullable=True)

    # ── Sévérité combinée ────────────────────────────────────────────────────
    # "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    severity        = Column(String(20), default="NONE", nullable=False)

    # ── Contexte temporel (pour stats et dashboard) ──────────────────────────
    submission_hour     = Column(Integer, nullable=True)   # 0-23
    submission_weekday  = Column(Integer, nullable=True)   # 0=Lundi … 6=Dimanche
    is_weekend          = Column(Boolean, nullable=True)
    is_out_of_hours     = Column(Boolean, nullable=True)
    tickets_today       = Column(Integer, nullable=True)   # Nb de tickets ce jour pour cet employé

    # ── Explication lisible ──────────────────────────────────────────────────
    explanation     = Column(Text, nullable=True)

    # ── Source du ticket (copie pour faciliter les requêtes) ─────────────────
    ticket_source   = Column(String(30), nullable=True)   # ITOP / EMPLOYEE_PORTAL / ADMIN_SIMULATION

    # ── Gestion du statut (v3.0) ─────────────────────────────────────────────
    # PENDING / VALIDATED / IGNORED
    status          = Column(String(20), default="PENDING", server_default="PENDING")
    resolved_at     = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamp d'analyse ──────────────────────────────────────────────────
    analyzed_at     = Column(DateTime(timezone=True), server_default=func.now())
