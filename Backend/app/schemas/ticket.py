# app/schemas/ticket.py

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional, Any, Dict
from enum import Enum


class TicketStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class ClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_level: str
    confidence: float
    probabilities: Dict[str, float]
    explanation: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    model_version: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    # Audit fields
    risk_score_rules: Optional[int] = None
    decision_source: Optional[str] = None
    consistency_status: Optional[str] = None
    consistency_message: Optional[str] = None
    triggered_rules: Optional[List[str]] = None
    recommended_action: Optional[str] = None
    confidence_level_label: Optional[str] = None


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None

    # Relationship to ClassificationResult
    classification: Optional[ClassificationResponse] = None

    # Flattened AI fields for easier frontend consumption
    # We'll use @property or model_validator in the future if needed, 
    # but for now let's keep them as optional fields that can be populated.
    ai_level: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_probabilities: Optional[Dict[str, float]] = None
    ai_risk_score: Optional[int] = None
    ai_consistency: Optional[str] = None
    ai_recommended_action: Optional[str] = None
    
    # Explainability shortcuts
    ai_explanation: Optional[str] = None
    ai_risk_factors: Optional[Dict[str, Any]] = None
    ai_source: Optional[str] = None