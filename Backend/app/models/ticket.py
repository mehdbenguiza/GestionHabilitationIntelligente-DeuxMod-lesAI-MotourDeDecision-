# app/models/ticket.py

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class TicketStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.NEW)
    
    # Informations demandeur
    employee_id = Column(String(50), nullable=False)
    employee_name = Column(String(100))
    employee_email = Column(String(100))
    team_name = Column(String(50))
    role = Column(String(50))
    
    # Détails de la demande
    description = Column(Text)
    requested_environments = Column(JSON)
    requested_access_details = Column(JSON)
    
    # Champs d'assignation
    assigned_to = Column(String(50), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Motif de rejet
    rejected_reason = Column(Text, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String(100), nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    synced_at = Column(DateTime(timezone=True))

    # ✅ Relation avec le moteur IA
    classification = relationship("ClassificationResult", backref="ticket", uselist=False, cascade="all, delete-orphan")

    # ✅ Champs dénormalisés pour la performance (Supervision/Filtres)
    ai_level              = Column(String(20), nullable=True)
    ai_confidence         = Column(Float, nullable=True)
    ai_probabilities      = Column(JSON, nullable=True)
    ai_risk_score         = Column(Integer, nullable=True)
    ai_consistency        = Column(String(20), nullable=True)
    ai_recommended_action = Column(String(50), nullable=True)