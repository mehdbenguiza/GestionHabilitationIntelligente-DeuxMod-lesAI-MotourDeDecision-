# app/api/endpoints/tickets.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.ticket import TicketResponse
from app.services.ticket_service import TicketService
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.ticket import TicketStatus

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_service(db: Session = Depends(get_db)) -> TicketService:
    return TicketService(db)


@router.get("/sync")
async def sync_tickets(
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Synchronise les tickets depuis iTop"""
    return ticket_service.sync_from_itop()


@router.get("/", response_model=List[TicketResponse])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    team: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Liste des tickets avec filtres optionnels"""
    return ticket_service.get_all_tickets(status, team, skip, limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Détail d'un ticket"""
    return ticket_service.get_ticket_by_id(ticket_id)


@router.post("/{ticket_id}/approve")
async def approve_ticket(
    ticket_id: int,
    resolution: Optional[str] = "Demande approuvée",
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Approuver un ticket"""
    ticket = ticket_service.approve_ticket(ticket_id, current_user, resolution)
    return {"message": "Ticket approuvé", "ticket_id": ticket.id}


@router.post("/{ticket_id}/reject")
async def reject_ticket(
    ticket_id: int,
    reason: str = Query(..., description="Motif du rejet (obligatoire)"),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Rejeter un ticket avec motif obligatoire"""
    ticket = ticket_service.reject_ticket(ticket_id, reason, current_user)
    return {"message": "Ticket rejeté", "ticket_id": ticket.id, "reason": reason}


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
        "escalated_to": escalate_to
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