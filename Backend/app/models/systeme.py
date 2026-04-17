# app/models/systeme.py
"""
Référentiel des Systèmes d'Information de la banque.
Chaque système regroupe un périmètre applicatif avec ses environnements associés.
Ce modèle remplace le besoin d'un vrai annuaire ITSM en simulation.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Systeme(Base):
    __tablename__ = "systemes"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50), unique=True, nullable=False, index=True)   # ex: CORE_BANKING
    nom         = Column(String(100), nullable=False)                           # ex: Core Banking
    description = Column(Text, nullable=True)
    # Liste des applications gérées par ce système (JSON array)
    applications = Column(JSON, nullable=False, default=list)
    # Liste des environnements supportés (JSON array)
    environments = Column(JSON, nullable=False, default=list)
    # Responsable technique du système (pour le CC des emails)
    responsable_email = Column(String(100), nullable=True)
    # Niveau de sensibilité global du système
    sensibilite = Column(String(20), nullable=False, default="SENSITIVE")  # BASE | SENSITIVE | CRITICAL
    actif       = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relation vers les profils d'accès créés sur ce système
    access_profiles = relationship("AccessProfile", back_populates="systeme", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Systeme code={self.code} nom={self.nom}>"
