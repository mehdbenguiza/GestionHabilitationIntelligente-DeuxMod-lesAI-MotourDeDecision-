from sqlalchemy import Column, String, Float, Integer
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id         = Column(String(50), primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=True)
    team       = Column(String(50),  nullable=True)
    role       = Column(String(50),  nullable=True)
    seniority  = Column(String(20),  default="junior")  # 'junior' | 'senior'

    # ── V3.0 : Trust Score (Réputation Employé) ──────────────────────────────
    trust_score        = Column(Float,   default=100.0)  # 0-100 (100=fiable, 0=suspect)
    total_requests     = Column(Integer, default=0)       # Nb total de demandes soumises
    approved_requests  = Column(Integer, default=0)       # Nb approuvées
    rejected_requests  = Column(Integer, default=0)       # Nb rejetées
