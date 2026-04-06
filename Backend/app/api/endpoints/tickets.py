# app/api/endpoints/tickets.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from app.database import get_db
from app.services.ticket_service import TicketService
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.ticket import TicketStatus, Ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_service(db: Session = Depends(get_db)) -> TicketService:
    return TicketService(db)


def serialize_ticket(ticket: Ticket) -> dict:
    """
    ✅ Sérialise un ticket en dict incluant les champs IA plats.
    Pydantic `from_orm` ne gère pas les attributs dynamiques ajoutés après construction,
    donc on sérialise manuellement pour garantir que ai_level, ai_confidence, ai_probabilities
    soient toujours présents.
    """
    classification = getattr(ticket, 'classification', None)

    result = {
        "id": ticket.id,
        "ref": ticket.ref,
        "status": ticket.status.value if hasattr(ticket.status, 'value') else ticket.status,
        "employee_id": ticket.employee_id,
        "employee_name": ticket.employee_name,
        "employee_email": ticket.employee_email,
        "team_name": ticket.team_name,
        "role": ticket.role,
        "description": ticket.description,
        "requested_environments": ticket.requested_environments,
        "requested_access_details": ticket.requested_access_details,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        "assigned_to": ticket.assigned_to,
        "assigned_at": ticket.assigned_at.isoformat() if ticket.assigned_at else None,
        "rejected_reason": ticket.rejected_reason,
        "rejected_by": ticket.rejected_by,
        "rejected_at": ticket.rejected_at.isoformat() if ticket.rejected_at else None,

        # ✅ Champs IA plats (toujours présents, même si None)
        "ai_level": getattr(ticket, 'ai_level', None),
        "ai_confidence": getattr(ticket, 'ai_confidence', None),
        "ai_probabilities": getattr(ticket, 'ai_probabilities', None),

        # Objet classification complet imbriqué
        "classification": {
            "predicted_level": classification.predicted_level,
            "confidence": round(classification.confidence, 2),
            "probabilities": classification.probabilities,
            "model_version": classification.model_version,
            "processed_at": classification.processed_at.isoformat() if classification.processed_at else None,
        } if classification else None,
    }
    return result


@router.get("/sync")
async def sync_tickets(
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Synchronise les tickets depuis iTop"""
    return ticket_service.sync_from_itop()


@router.get("/", response_model=None)
async def get_tickets(
    status: Optional[TicketStatus] = None,
    team: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Liste des tickets avec filtres optionnels — inclut les données IA"""
    tickets = ticket_service.get_all_tickets(status, team, skip, limit)
    return [serialize_ticket(t) for t in tickets]


@router.get("/{ticket_id}", response_model=None)
async def get_ticket(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Détail d'un ticket — inclut les données IA"""
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    return serialize_ticket(ticket)


@router.post("/{ticket_id}/approve")
async def approve_ticket(
    ticket_id: int,
    resolution: Optional[str] = "Demande approuvée",
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Approuver un ticket"""
    ticket = ticket_service.approve_ticket(ticket_id, current_user, resolution)
    return {"message": "Ticket approuvé", "ticket_id": ticket.id, "ticket": serialize_ticket(ticket)}


@router.post("/{ticket_id}/reject")
async def reject_ticket(
    ticket_id: int,
    reason: str = Query(..., description="Motif du rejet (obligatoire)"),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Rejeter un ticket avec motif obligatoire"""
    ticket = ticket_service.reject_ticket(ticket_id, reason, current_user)
    return {"message": "Ticket rejeté", "ticket_id": ticket.id, "reason": reason, "ticket": serialize_ticket(ticket)}


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: int,
    escalate_to: str = Query(..., description="ADMIN ou SUPER_ADMIN"),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Escalader un ticket vers un niveau supérieur"""
    ticket = ticket_service.escalate_ticket(ticket_id, escalate_to, current_user)
    return {
        "message": f"Ticket escaladé vers {escalate_to}",
        "ticket_id": ticket.id,
        "escalated_to": escalate_to,
        "ticket": serialize_ticket(ticket)
    }


# ==================== ENDPOINTS DE SIMULATION ====================

@router.post("/simulate/create", include_in_schema=False)
async def simulate_create_ticket(
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Crée un ticket simulé pour tester le workflow"""
    return ticket_service.simulate_create_ticket()


@router.post("/simulate/batch/{count}", include_in_schema=False)
async def simulate_batch_tickets(
    count: int = 10,
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Crée plusieurs tickets simulés en une fois"""
    return ticket_service.simulate_batch_tickets(count)