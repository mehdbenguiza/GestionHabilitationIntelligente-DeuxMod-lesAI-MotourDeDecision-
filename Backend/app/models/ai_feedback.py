# app/models/ai_feedback.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import hashlib


def compute_profile_signature(application: str, environment: str, access_type: str, team: str, resource: str = "") -> str:
    """
    Calcule une signature unique pour un profil de ticket.
    Deux tickets avec la même application/environment/access_type/team
    partagent la même signature → la même correction s'applique.
    """
    raw = f"{application.upper()}|{environment.upper()}|{access_type.upper()}|{team.upper()}|{resource.upper()}"
    return hashlib.md5(raw.encode()).hexdigest()


class AIFeedback(Base):
    """
    Vote d'un Admin / Super Admin sur la classification IA d'un ticket spécifique.
    - classification_vote : l'IA a-t-elle bien classé le niveau ?
    - reason_vote         : l'explication donnée est-elle correcte ?
    - Si dislike + corrected_level → une correction est créée dans AICorrection
    """
    __tablename__ = "ai_feedback"

    id                  = Column(Integer, primary_key=True, index=True)
    ticket_id           = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    classification_id   = Column(Integer, ForeignKey("classification_results.id", ondelete="SET NULL"), nullable=True)

    reviewer            = Column(String(100), nullable=False)      # username de l'admin
    classification_vote = Column(String(10), nullable=False)       # "like" | "dislike"
    reason_vote         = Column(String(10), nullable=True)        # "like" | "dislike" | null

    # Fourni uniquement en cas de dislike sur la classification
    corrected_level     = Column(String(20), nullable=True)        # "BASE" | "SENSITIVE" | "CRITICAL"
    corrected_reason    = Column(Text, nullable=True)              # Explication humaine

    created_at          = Column(DateTime(timezone=True), server_default=func.now())


class AICorrection(Base):
    """
    Bibliothèque de corrections humaines indexée par profil de ticket.
    Consultée en PREMIER lors de chaque classification :
    si le profil entrant correspond → la correction est appliquée directement.
    """
    __tablename__ = "ai_corrections"

    id                  = Column(Integer, primary_key=True, index=True)

    # Clé de recherche : signature du profil
    profile_signature   = Column(String(64), nullable=False, index=True, unique=True)

    # Détails du profil pour lisibilité / debug
    application         = Column(String(50), nullable=False)
    environment         = Column(String(20), nullable=False)
    access_type         = Column(String(30), nullable=False)
    team                = Column(String(50), nullable=False)
    resource            = Column(String(60), nullable=True)

    # La correction
    corrected_level     = Column(String(20), nullable=False)       # "BASE"|"SENSITIVE"|"CRITICAL"
    corrected_reason    = Column(Text, nullable=False)             # Raison humaine

    # Traçabilité
    source_ticket_id    = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True)
    reviewer            = Column(String(100), nullable=False)

    # Statistiques
    usage_count         = Column(Integer, default=0)               # Fois où appliquée
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at        = Column(DateTime(timezone=True), nullable=True)
