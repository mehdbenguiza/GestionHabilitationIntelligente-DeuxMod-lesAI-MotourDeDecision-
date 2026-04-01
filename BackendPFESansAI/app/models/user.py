from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from app.database import Base
import enum
from datetime import datetime

class Role(enum.Enum):
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class DashboardUser(Base):
    __tablename__ = "dashboard_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    fullName = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    passwordHash = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.ADMIN)
    isActive = Column(Boolean, default=True)
    lastLogin = Column(DateTime)
    createdAt = Column(DateTime, default=datetime.utcnow)
    lastLoginIP = Column(String(50))
    lastSessionDuration = Column(String(50), default="0 min")
    
    # ✅ NOUVEAU : Refresh token
    refresh_token = Column(String(500), nullable=True)
    refresh_token_created_at = Column(DateTime, nullable=True)