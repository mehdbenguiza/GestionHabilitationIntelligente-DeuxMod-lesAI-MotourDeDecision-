# app/services/ticket_service.py

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
from app.repositories.ticket_repository import TicketRepository
from app.services.itop_service import ITopService
from app.services.ai_service import ai_service
from app.models.classification_result import ClassificationResult
from app.models.ticket import Ticket, TicketStatus
from app.models.user import DashboardUser
from app.core.exceptions import NotFoundException, BusinessException
from app.core.config import settings


def _enrich_ticket_with_ai(ticket: Ticket, db: Session) -> Ticket:
    """
    Attach the latest ClassificationResult to a ticket and expose
    ai_level / ai_confidence / ai_probabilities as flat attributes
    that Pydantic will pick up in TicketResponse.
    """
    latest_classification = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.ticket_id == ticket.id)
        .order_by(ClassificationResult.processed_at.desc())
        .first()
    )

    if latest_classification:
        ticket.classification = latest_classification
        # ✅ Ajouter les raccourcis plats pour le frontend
        ticket.ai_level = latest_classification.predicted_level
        ticket.ai_confidence = round(latest_classification.confidence, 2)
        ticket.ai_probabilities = latest_classification.probabilities or {}
    else:
        ticket.classification = None
        ticket.ai_level = None
        ticket.ai_confidence = None
        ticket.ai_probabilities = None

    return ticket


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.itop_service = ITopService()

    def get_all_tickets(self, status: Optional[TicketStatus] = None, team: Optional[str] = None,
                        skip: int = 0, limit: int = 100) -> List[Ticket]:
        query = self.db.query(Ticket)
        if status:
            query = query.filter(Ticket.status == status)
        if team:
            query = query.filter(Ticket.team_name == team)
        tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

        # ✅ CORRECTION BUG 4 : Enrichir CHAQUE ticket avec ses données IA
        for ticket in tickets:
            _enrich_ticket_with_ai(ticket, self.db)

        return tickets

    def get_ticket_by_id(self, ticket_id: int) -> Ticket:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket")

        # ✅ CORRECTION BUG 3 : Utiliser la fonction d'enrichissement commune
        _enrich_ticket_with_ai(ticket, self.db)

        return ticket

    def sync_from_itop(self) -> Dict[str, Any]:
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
                ai_service.classify_and_save(self.db, new_ticket)
                synced_count += 1
                new_tickets.append(new_ticket)

        self.db.commit()

        return {
            "message": f"{synced_count} nouveaux tickets synchronisés",
            "total": len(itop_tickets),
            "tickets": [t.id for t in new_tickets]
        }

    def approve_ticket(self, ticket_id: int, current_user: DashboardUser, resolution: str = "Demande approuvée") -> Ticket:
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.approve_ticket(ticket_id)
        self.itop_service.update_ticket_status(ticket.ref, "approved", resolution)
        _enrich_ticket_with_ai(ticket, self.db)
        return ticket

    def reject_ticket(self, ticket_id: int, reason: str, current_user: DashboardUser) -> Ticket:
        if not reason or not reason.strip():
            raise BusinessException("Un motif de rejet est obligatoire")
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.reject_ticket(ticket_id, reason, current_user.username)
        self.itop_service.update_ticket_status(ticket.ref, "rejected", reason)
        _enrich_ticket_with_ai(ticket, self.db)
        return ticket

    def escalate_ticket(self, ticket_id: int, escalate_to: str, current_user: DashboardUser) -> Ticket:
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.assign_ticket(ticket_id, escalate_to)
        _enrich_ticket_with_ai(ticket, self.db)
        return ticket

    def simulate_create_ticket(self) -> Dict[str, Any]:
        """Crée un ticket simulé pour le développement avec classification IA"""
        if settings.ENVIRONMENT != "development":
            raise BusinessException("Disponible uniquement en mode développement", 403)

        teams = ["MOE", "MOA", "RESEAU", "SECURITE", "TEST_FACTORY", "DATA", "MXP"]
        envs = ["DEV2", "QL2", "DVR", "CRT", "INV", "PRD"]
        access_types = ["READ", "WRITE", "EXECUTE", "UPDATE", "DELETE", "FULL_ACCESS"]
        first_names = ["Mehdi", "Sara", "Omar", "Leila", "Karim", "Nadia", "Ahmed", "Hela"]
        last_names = ["Ben Guiza", "Ben Ali", "Haddad", "Khelil", "Trabelsi", "Gharbi"]

        random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        random_team = random.choice(teams)
        
        # Add roles logic
        ROLES_PER_TEAM = {
            "MOE": ["DEVELOPPEUR", "TECH_LEAD", "CHEF_DE_PROJET", "STAGIAIRE"],
            "MOA": ["BUSINESS_ANALYST", "PRODUCT_OWNER", "CHEF_DE_PROJET"],
            "RESEAU": ["INGENIEUR_RESEAU", "ADMINISTRATEUR", "STAGIAIRE"],
            "SECURITE": ["ANALYSTE_SOC", "RSSI", "PENTESTER"],
            "TEST_FACTORY": ["TESTEUR_QA", "TEST_LEAD", "AUTOMATICIEN"],
            "DATA": ["DATA_SCIENTIST", "DATA_ENGINEER", "DATA_ANALYST"],
            "MXP": ["INTEGRATEUR", "CHEF_DE_PROJET", "DEVELOPPEUR_MXP"]
        }
        random_role = random.choice(ROLES_PER_TEAM[random_team])
        
        random_envs = random.sample(envs, random.randint(1, 2))
        random_access = random.sample(access_types, random.randint(1, 2))
        criticite = random.choice(["BASE", "SENSITIVE", "CRITICAL"])

        new_ticket = self.ticket_repo.create({
            "ref": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
            "status": TicketStatus.NEW,
            "employee_id": f"EMP-{random.randint(1000, 9999)}",
            "employee_name": random_name,
            "employee_email": f"{random_name.lower().replace(' ', '.')}@biat-it.com.tn",
            "team_name": random_team,
            "role": random_role,
            "description": f"Demande d'accès en {', '.join(random_access)} sur {', '.join(random_envs)}",
            "requested_environments": random_envs,
            "requested_access_details": {
                "access_types": random_access,
                "criticite": criticite,
                "justification": "Projet de fin d'études - tests"
            }
        })

        # Classification IA automatique
        ai_result = ai_service.classify_and_save(self.db, new_ticket)

        return {
            "message": "Ticket simulé créé avec succès",
            "ticket": {
                "id": new_ticket.id,
                "ref": new_ticket.ref,
                "employee_name": new_ticket.employee_name,
                "team": new_ticket.team_name,
                "role": new_ticket.role,
                "environments": new_ticket.requested_environments,
                "access": new_ticket.requested_access_details,
                "ai_classification": {
                    "level": ai_result["classification"]["level"],
                    "confidence": ai_result["classification"]["confidence"],
                    "probabilities": ai_result["classification"]["probabilities"],
                    "assigned_to": ai_result["ticket_updated"]["assigned_to"]
                }
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