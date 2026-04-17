# app/models/access_profile.py
"""
Profil d'accès généré automatiquement après approbation d'un ticket.
Représente les credentials créés pour l'employé sur le système cible.
Le mot de passe temporaire est stocké en clair UNIQUEMENT le temps de l'envoi email,
puis effacé (temp_password_cleared=True).
"""

import enum
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProfileStatus(str, enum.Enum):
    ACTIVE  = "ACTIVE"    # Profil actif et utilisable
    REVOKED = "REVOKED"   # Révoqué manuellement par un admin
    EXPIRED = "EXPIRED"   # Expiré (pour usage futur si durée de vie ajoutée)


class AccessProfile(Base):
    __tablename__ = "access_profiles"

    id          = Column(Integer, primary_key=True, index=True)

    # --- Relations ---
    ticket_id   = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    system_id   = Column(Integer, ForeignKey("systemes.id", ondelete="SET NULL"), nullable=True, index=True)

    # --- Identité du compte ---
    account_name  = Column(String(100), nullable=False, index=True)  # ex: m.benguiza
    password_hash = Column(String(255), nullable=False)               # bcrypt hash
    temp_password = Column(String(100), nullable=True)                # En clair, nettoyé après envoi email
    temp_password_cleared = Column(Boolean, default=False)            # True une fois l'email envoyé

    # --- Périmètre d'accès accordé ---
    application   = Column(String(100), nullable=True)   # ex: T24
    environments  = Column(JSON, nullable=True)           # ex: ["PRD", "UAT"]
    access_types  = Column(JSON, nullable=True)           # ex: ["READ", "WRITE"]
    resource      = Column(String(100), nullable=True)    # ex: TRANSACTIONS_FINANCIERES

    # --- Statut ---
    status        = Column(Enum(ProfileStatus), default=ProfileStatus.ACTIVE, index=True)

    # --- Métadonnées ---
    created_by    = Column(String(100), nullable=True)    # username de l'admin qui a approuvé
    revoked_by    = Column(String(100), nullable=True)
    revoked_reason= Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at    = Column(DateTime(timezone=True), nullable=True)
    expires_at    = Column(DateTime(timezone=True), nullable=True)  # NULL = permanent

    # --- Email envoyé ---
    notification_sent    = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)

    # --- Relations ORM --- (string refs pour éviter les dépendances circulaires)
    ticket   = relationship("Ticket",   foreign_keys=[ticket_id],   backref="access_profile",  lazy="select")
    employee = relationship("Employee", foreign_keys=[employee_id], backref="access_profiles", lazy="select")
    systeme  = relationship("Systeme",  back_populates="access_profiles",                      lazy="select")

    def __repr__(self):
        return f"<AccessProfile account={self.account_name} status={self.status}>"
