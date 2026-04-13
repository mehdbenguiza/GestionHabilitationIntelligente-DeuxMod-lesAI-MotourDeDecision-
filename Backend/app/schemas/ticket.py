# app/schemas/ticket.py

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional, Any, Dict
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


    explanation: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    
    # Audit Gold
    risk_score_rules: Optional[int] = None
    decision_source: Optional[str] = None
    consistency_status: Optional[str] = None
    consistency_message: Optional[str] = None
    triggered_rules: Optional[List[str]] = None
    recommended_action: Optional[str] = None
    confidence_level_label: Optional[str] = None
    
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None

    # ✅ Données de classification embarquées (issues du ClassificationResult)
    classification: Optional[ClassificationInfo] = None

    # ✅ NOUVEAUX CHAMPS : Raccourcis pratiques pour le frontend
    # Ces champs sont calculés à partir de `classification` dans le validator
    ai_level: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_probabilities: Optional[Dict[str, float]] = None
    
    # Raccourcis Audit
    ai_risk_score: Optional[int] = None
    ai_consistency: Optional[str] = None
    ai_recommended_action: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('ai_level', 'ai_confidence', 'ai_probabilities', mode='before')
    @classmethod
    def set_ai_fields(cls, v):
        # Ces champs sont peuplés manuellement dans le service
        return v