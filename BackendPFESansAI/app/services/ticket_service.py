# app/services/ticket_service.py

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
from app.repositories.ticket_repository import TicketRepository
from app.services.itop_service import ITopService
from app.models.ticket import Ticket, TicketStatus
from app.models.user import DashboardUser
from app.core.exceptions import NotFoundException, ForbiddenException, BusinessException
from app.core.config import settings

class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.itop_service = ITopService()

    def get_all_tickets(self, status: Optional[TicketStatus] = None, team: Optional[str] = None,
                        skip: int = 0, limit: int = 100) -> List[Ticket]:
        """Récupère tous les tickets avec filtres"""
        query = self.db.query(Ticket)
        if status:
            query = query.filter(Ticket.status == status)
        if team:
            query = query.filter(Ticket.team_name == team)
        return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

    def get_ticket_by_id(self, ticket_id: int) -> Ticket:
        """Récupère un ticket par son ID"""
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket")
        return ticket

    def sync_from_itop(self) -> Dict[str, Any]:
        """Synchronise les tickets depuis iTop"""
        itop_tickets = self.itop_service.fetch_tickets()
        synced_count = 0
        new_tickets = []

        for itop_ticket in itop_tickets:
            existing = self.ticket_repo.get_by_ref(itop_ticket["ref"])
            if not existing:
                new_ticket = self.ticket_repo.create({
                    "ref": itop_ticket["ref"],
                    "status": TicketStatus.NEW,
                    "employee_id": itop_ticket["caller_id"],
                    "employee_name": itop_ticket.get("caller_name"),
                    "employee_email": itop_ticket.get("caller_email"),
                    "team_name": itop_ticket.get("team"),
                    "description": itop_ticket.get("description"),
                    "requested_environments": itop_ticket.get("requested_env", []),
                    "requested_access_details": itop_ticket.get("requested_access", [])
                })
                synced_count += 1
                new_tickets.append(new_ticket)

        return {
            "message": f"{synced_count} nouveaux tickets synchronisés",
            "total": len(itop_tickets),
            "tickets": [t.id for t in new_tickets]
        }

    def approve_ticket(self, ticket_id: int, current_user: DashboardUser, resolution: str = "Demande approuvée") -> Ticket:
        """Approuve un ticket"""
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.approve_ticket(ticket_id)
        self.itop_service.update_ticket_status(ticket.ref, "approved", resolution)
        return ticket

    def reject_ticket(self, ticket_id: int, reason: str, current_user: DashboardUser) -> Ticket:
        """Rejette un ticket avec motif"""
        if not reason or not reason.strip():
            raise BusinessException("Un motif de rejet est obligatoire")

        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.reject_ticket(ticket_id, reason, current_user.username)
        self.itop_service.update_ticket_status(ticket.ref, "rejected", reason)
        return ticket

    def escalate_ticket(self, ticket_id: int, escalate_to: str, current_user: DashboardUser) -> Ticket:
        """Escalade un ticket vers un niveau supérieur"""
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.assign_ticket(ticket_id, escalate_to)
        return ticket

    def simulate_create_ticket(self) -> Dict[str, Any]:
        """Crée un ticket simulé pour le développement"""
        if settings.ENVIRONMENT != "development":
            raise BusinessException("Disponible uniquement en mode développement", 403)

        teams = ["DÉVELOPPEMENT", "SÉCURITÉ", "DBA", "RÉSEAU", "SUPPORT", "INTÉGRATION"]
        envs = ["T24_DEV2", "T24_QL2", "T24_CRT", "PRD"]
        access_types = ["LECTURE", "ÉCRITURE", "ADMIN", "EXÉCUTION"]
        first_names = ["Mehdi", "Sara", "Omar", "Leila", "Karim", "Nadia", "Ahmed", "Hela"]
        last_names = ["Ben Guiza", "Ben Ali", "Haddad", "Khelil", "Trabelsi", "Gharbi"]

        random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        random_team = random.choice(teams)
        random_envs = random.sample(envs, random.randint(1, 2))
        random_access = random.sample(access_types, random.randint(1, 2))
        criticite = random.choice(["BASE", "SENSIBLE", "CRITIQUE"])

        new_ticket = self.ticket_repo.create({
            "ref": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
            "status": TicketStatus.NEW,
            "employee_id": f"EMP-{random.randint(1000, 9999)}",
            "employee_name": random_name,
            "employee_email": f"{random_name.lower().replace(' ', '.')}@biat-it.com.tn",
            "team_name": random_team,
            "description": f"Demande d'accès en {', '.join(random_access)} sur {', '.join(random_envs)} pour le projet PFE",
            "requested_environments": random_envs,
            "requested_access_details": {
                "access_types": random_access,
                "criticite": criticite,
                "justification": "Projet de fin d'études - tests"
            }
        })

        return {
            "message": "Ticket simulé créé avec succès",
            "ticket": {
                "id": new_ticket.id,
                "ref": new_ticket.ref,
                "employee_name": new_ticket.employee_name,
                "team": new_ticket.team_name,
                "environments": new_ticket.requested_environments,
                "access": new_ticket.requested_access_details
            }
        }

    def simulate_batch_tickets(self, count: int) -> Dict[str, Any]:
        """Crée plusieurs tickets simulés"""
        if settings.ENVIRONMENT != "development":
            raise BusinessException("Disponible uniquement en mode développement", 403)

        created = []
        for _ in range(min(count, 50)):
            result = self.simulate_create_ticket()
            created.append(result["ticket"])

        return {
            "message": f"{len(created)} tickets simulés créés",
            "tickets": created
        }