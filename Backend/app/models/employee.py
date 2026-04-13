from sqlalchemy import Column, String
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    team = Column(String(50), nullable=True)
    role = Column(String(50), nullable=True)
    seniority = Column(String(20), default="junior")  # 'junior' or 'senior'
