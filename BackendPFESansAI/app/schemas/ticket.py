# app/schemas/ticket.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

class TicketStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"

class TicketBase(BaseModel):
    ref: str
    employee_id: str
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    team_name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    requested_environments: Optional[List[str]] = None
    requested_access_details: Optional[Any] = None

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None

class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # ✅ Champs d'assignation
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    
    # ✅ Champs de rejet
    rejected_reason: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True