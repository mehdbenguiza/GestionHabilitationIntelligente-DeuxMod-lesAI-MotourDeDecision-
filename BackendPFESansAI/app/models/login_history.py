from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("dashboard_users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # "Connexion", "Déconnexion", "Modification profil"
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(255), nullable=True)

    # Relation
    user = relationship("DashboardUser", backref="login_history")