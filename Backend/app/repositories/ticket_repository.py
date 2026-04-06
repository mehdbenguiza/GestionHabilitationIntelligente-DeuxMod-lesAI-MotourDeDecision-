# app/repositories/ticket_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.ticket import Ticket, TicketStatus
from datetime import datetime

class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: Session):
        super().__init__(db, Ticket)

    def get_by_ref(self, ref: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.ref == ref).first()

    def get_by_status(self, status: TicketStatus, skip: int = 0, limit: int = 100) -> List[Ticket]:
        return self.db.query(Ticket).filter(Ticket.status == status).offset(skip).limit(limit).all()

    def get_by_team(self, team_name: str, skip: int = 0, limit: int = 100) -> List[Ticket]:
        return self.db.query(Ticket).filter(Ticket.team_name == team_name).offset(skip).limit(limit).all()

    def update_status(self, ticket_id: int, status: TicketStatus) -> Optional[Ticket]:
        return self.update(ticket_id, {"status": status})

    def reject_ticket(self, ticket_id: int, reason: str, rejected_by: str) -> Optional[Ticket]:
        return self.update(ticket_id, {
            "status": TicketStatus.REJECTED,
            "rejected_reason": reason,
            "rejected_at": datetime.utcnow(),
            "rejected_by": rejected_by
        })

    def approve_ticket(self, ticket_id: int) -> Optional[Ticket]:
        return self.update(ticket_id, {"status": TicketStatus.APPROVED})

    def assign_ticket(self, ticket_id: int, assigned_to: str) -> Optional[Ticket]:
        return self.update(ticket_id, {
            "status": TicketStatus.ASSIGNED,
            "assigned_to": assigned_to,
            "assigned_at": datetime.utcnow()
        })