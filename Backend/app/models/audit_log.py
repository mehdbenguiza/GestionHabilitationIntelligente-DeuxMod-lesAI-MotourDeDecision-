from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, nullable=True)
    ticket_ref = Column(String(50), nullable=True)
    acteur_name = Column(String(100), nullable=False)
    acteur_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    categorie = Column(String(50), nullable=False, default="Ticket")
    environnement = Column(String(50), nullable=True)
    resultat = Column(String(50), nullable=False, default="Succès")
    niveau_acces = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
