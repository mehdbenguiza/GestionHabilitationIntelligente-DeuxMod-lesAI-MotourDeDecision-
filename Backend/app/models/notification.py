# app/models/notification.py

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), default="info") # info, warning, danger, success
    
    # "ADMIN,SUPER_ADMIN" ou "SUPER_ADMIN"
    target_roles = Column(String(100), nullable=False)
    
    # Stocke une liste JSON format string des IDs des utilisateurs qui l'ont lue
    read_by = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
