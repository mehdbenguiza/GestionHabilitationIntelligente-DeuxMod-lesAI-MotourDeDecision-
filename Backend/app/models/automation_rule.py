
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    equipe = Column(String(100), nullable=False)
    roles = Column(JSON, nullable=False)  # List of roles
    environnements = Column(JSON, nullable=False)  # List of envs
    acces_par_defaut = Column(JSON, nullable=False)  # List of {nom, niveau}
    actif = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
