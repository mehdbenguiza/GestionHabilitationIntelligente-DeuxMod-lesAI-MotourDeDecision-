# app/services/ticket_service.py

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
from app.repositories.ticket_repository import TicketRepository
from app.services.itop_service import ITopService
from app.services.ai_service import ai_service
from app.services.profile_service import profile_service
from app.services.audit_service import audit_service
from app.models.classification_result import ClassificationResult
from app.models.ticket import Ticket, TicketStatus
from app.models.user import DashboardUser
from app.models.employee import Employee
from app.core.exceptions import NotFoundException, BusinessException
from app.core.config import settings


def _enrich_ticket_with_ai(ticket: Ticket) -> Ticket:
    """
    Remplir les champs plats 'ai_xxx' du ticket à partir de sa classification.
    Cela évite de recalculer ces champs partout ailleurs.
    """
    latest = ticket.classification
    if latest:
        ticket.ai_level = latest.predicted_level
        ticket.ai_confidence = round(latest.confidence, 2)
        ticket.ai_probabilities = latest.probabilities or {}
        ticket.ai_risk_score = latest.risk_score_rules
        ticket.ai_consistency = latest.consistency_status
        ticket.ai_recommended_action = latest.recommended_action
        
        # Champs Explainability
        ticket.ai_explanation = latest.explanation
        ticket.ai_risk_factors = latest.risk_factors
        ticket.ai_source = latest.source
    else:
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

        for ticket in tickets:
            _enrich_ticket_with_ai(ticket)

        return tickets

    def get_ticket_by_id(self, ticket_id: int) -> Ticket:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket")

        _enrich_ticket_with_ai(ticket)

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

        # ── 1. Créer le profil d'accès + envoyer l'email d'approbation (simulation iTop) ──
        try:
            access_profile = profile_service.create_profile_from_ticket(
                db          = self.db,
                ticket      = ticket,
                approved_by = current_user.fullName or current_user.username,
            )
            # Notifier iTop (log ITSM)
            system_name = access_profile.systeme.nom if access_profile.systeme else "Système cible"
            self.itop_service.notify_ticket_approved(
                ticket      = ticket,
                profile     = access_profile,
                system_name = system_name,
                approved_by = current_user.fullName or current_user.username,
            )
        except Exception as e:
            # Ne pas bloquer l'approbation si la création du profil échoue
            print(f"⚠️ [PROFILE] Erreur création profil pour {ticket.ref}: {e}")

        # ── 2. Mettre à jour iTop ──
        self.itop_service.update_ticket_status(ticket.ref, "approved", resolution)
        _enrich_ticket_with_ai(ticket)

        # ── 3. Log Audit via AuditService ──
        audit_service.log_action(
            db=self.db,
            ticket_id=ticket.id,
            ticket_ref=ticket.ref,
            acteur_name=current_user.fullName or current_user.username,
            acteur_role=current_user.role.value,
            action="Approbation Ticket + Création Profil",
            environnement=ticket.requested_environments[0] if ticket.requested_environments else "Inconnu",
            niveau_acces=ticket.ai_level or "Inconnu",
            details={
                "resolution": resolution,
                "message": "Ticket approuvé — Profil d'accès créé — Email envoyé (simulation iTop)"
            }
        )
        self.db.commit()

        return ticket

    def reject_ticket(self, ticket_id: int, reason: str, current_user: DashboardUser) -> Ticket:
        if not reason or not reason.strip():
            raise BusinessException("Un motif de rejet est obligatoire")
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.reject_ticket(ticket_id, reason, current_user.username)

        # ── 1. Notifier l'employé du rejet par email (simulation iTop) ──
        try:
            profile_service.notify_rejection(
                db          = self.db,
                ticket      = ticket,
                reason      = reason,
                rejected_by = current_user.fullName or current_user.username,
            )
            self.itop_service.notify_ticket_rejected(
                ticket      = ticket,
                reason      = reason,
                rejected_by = current_user.fullName or current_user.username,
            )
        except Exception as e:
            print(f"⚠️ [EMAIL] Erreur notification rejet pour {ticket.ref}: {e}")

        # ── 2. Mettre à jour iTop ──
        self.itop_service.update_ticket_status(ticket.ref, "rejected", reason)
        _enrich_ticket_with_ai(ticket)

        # ── 3. Log Audit via AuditService ──
        audit_service.log_action(
            db=self.db,
            ticket_id=ticket.id,
            ticket_ref=ticket.ref,
            acteur_name=current_user.fullName or current_user.username,
            acteur_role=current_user.role.value,
            action="Rejet Ticket",
            resultat="Échec",
            environnement=ticket.requested_environments[0] if ticket.requested_environments else "Inconnu",
            niveau_acces=ticket.ai_level or "Inconnu",
            details={
                "motif": reason,
                "message": "Ticket rejeté — Email envoyé à l'employé (simulation iTop)"
            }
        )
        self.db.commit()

        return ticket

    def escalate_ticket(self, ticket_id: int, escalate_to: str, current_user: DashboardUser) -> Ticket:
        ticket = self.get_ticket_by_id(ticket_id)
        ticket = self.ticket_repo.assign_ticket(ticket_id, escalate_to)
        _enrich_ticket_with_ai(ticket)
        
        # Log Audit via AuditService
        audit_service.log_action(
            db=self.db,
            ticket_id=ticket.id,
            ticket_ref=ticket.ref,
            acteur_name=current_user.fullName or current_user.username,
            acteur_role=current_user.role.value,
            action="Escalade Ticket",
            resultat="Alerte",
            environnement=ticket.requested_environments[0] if ticket.requested_environments else "Inconnu",
            niveau_acces=ticket.ai_level or "Inconnu",
            details={"escaladé_vers": escalate_to, "message": "Nécessite validation supérieure"}
        )
        self.db.commit()
        
        return ticket

    def simulate_create_ticket(self) -> Dict[str, Any]:
        """Crée un ticket simulé pour le développement avec classification IA"""
        if settings.ENVIRONMENT != "development":
            raise BusinessException("Disponible uniquement en mode développement", 403)

        # ── Données de référence bancaires (identiques au dataset d'entraînement) ──
        BANKING_ROLES_PER_TEAM = {
            "MOE":          ["DEVELOPPEUR", "TECH_LEAD", "CHEF_DE_PROJET", "STAGIAIRE"],
            "MOA":          ["BUSINESS_ANALYST", "PRODUCT_OWNER", "CHEF_DE_PROJET"],
            "RESEAU":       ["INGENIEUR_RESEAU", "ADMINISTRATEUR", "STAGIAIRE"],
            "SECURITE":     ["ANALYSTE_SOC", "RSSI", "PENTESTER"],
            "TEST_FACTORY": ["TESTEUR_QA", "TEST_LEAD", "AUTOMATICIEN"],
            "DATA":         ["DATA_SCIENTIST", "DATA_ENGINEER", "DATA_ANALYST"],
            "MXP":          ["INTEGRATEUR", "CHEF_DE_PROJET", "INGENIEUR_EXPLOITATION"],
            "CONFORMITE":   ["OFFICIER_CONFORMITE", "AML_ANALYST"],
            "MONETIQUE":    ["INGENIEUR_MONETIQUE", "EXPLOITATION_MONETIQUE"],
            "TRADING":      ["FRONT_OFFICE_TRADER", "MIDDLE_OFFICE"],
            "AUDIT_INTERNE":["AUDITEUR_IT", "INSPECTEUR"],
        }
        BANKING_APPLICATIONS = ["T24", "MUREX", "SWIFT", "AML_TIDE", "E_BANKING", "CRM_SIEBEL", "QUANTARA"]
        BANKING_RESOURCES    = [
            "DONNEES_CLIENTS_SENSIBLES", "TRANSACTIONS_FINANCIERES",
            "LOGS_SECURITE", "CODE_SOURCE", "CLEFS_CRYPTOGRAPHIQUES",
            "DONNEES_CARRIERES_RH", "OTHER",
        ]
        BANKING_REASONS = [
            "incident_production_bloquant", "deploiement_version",
            "audit_reglementaire_bct", "demande_metier_urgente",
            "maintenance_preventive", "cloture_comptable_fin_de_mois",
        ]
        ALL_ENVS        = ["DEV2", "DVR", "TST", "QL2", "CRT", "UAT", "INV", "PRD"]
        ALL_ACCESS      = ["READ", "WRITE", "EXECUTE", "UPDATE", "DELETE", "FULL_ACCESS", "DBA_ACCESS"]

        employees = self.db.query(Employee).all()

        if employees:
            emp           = random.choice(employees)
            random_name   = emp.name
            random_team   = emp.team
            random_role   = emp.role or random.choice(BANKING_ROLES_PER_TEAM.get(emp.team, ["DEVELOPPEUR"]))
            employee_email = emp.email
            employee_id   = emp.id
            user_seniority = emp.seniority or random.choice(["junior", "senior"])
        else:
            first_names   = ["Mehdi", "Sara", "Omar", "Leila", "Karim", "Nadia", "Ahmed", "Hela"]
            last_names    = ["Ben Guiza", "Ben Ali", "Haddad", "Khelil", "Trabelsi", "Gharbi"]
            random_name   = f"{random.choice(first_names)} {random.choice(last_names)}"
            random_team   = random.choice(list(BANKING_ROLES_PER_TEAM.keys()))
            random_role   = random.choice(BANKING_ROLES_PER_TEAM[random_team])
            employee_email = f"{random_name.lower().replace(' ', '.')}@biat-it.com.tn"
            employee_id   = f"EMP-{random.randint(1000, 9999)}"
            user_seniority = random.choice(["junior", "senior"])

        random_envs    = random.sample(ALL_ENVS, random.randint(1, 2))
        random_access  = random.sample(ALL_ACCESS, random.randint(1, 2))
        application    = random.choices(
            BANKING_APPLICATIONS, weights=[20, 15, 10, 10, 20, 15, 10], k=1
        )[0]
        resource       = random.choices(
            BANKING_RESOURCES, weights=[15, 15, 15, 15, 10, 10, 20], k=1
        )[0]

        # ── Profil de risque selon la séniorité ─────────────────────────────────
        #
        # JUNIOR : inexpérimenté → demandes hors-scope, accès PRD/DELETE fréquents,
        #          rarement approuvé par le manager, motivations urgentes.
        #
        # SENIOR : maîtrise de son périmètre → accès DEV/TST cohérents, READ/WRITE
        #          majoritaires, manager souvent consulté, raisons légitimes.
        #
        # ALL_ENVS  = ["DEV2", "DVR", "TST", "QL2", "CRT", "UAT", "INV", "PRD"]
        # ALL_ACCESS= ["READ", "WRITE", "EXECUTE", "UPDATE", "DELETE", "FULL_ACCESS", "DBA_ACCESS"]

        if user_seniority == "junior":
            # Junior : PRD=27%, INV=20%, les accès dangereux sont communs
            env_weights    = [5, 5, 8, 8, 12, 15, 20, 27]
            access_weights = [10, 12, 8, 10, 20, 22, 18]
            approval_weights = [15, 25, 60]   # rarement approuvé
            reason_weights = [20, 15, 5, 25, 25, 10]  # beaucoup d'incidents/urgences
        else:
            # Senior : PRD quasi-impossible (0%), READ/WRITE dominent, plan approuvé
            env_weights    = [32, 24, 18, 14, 7, 4, 1, 0]
            access_weights = [42, 28, 14, 12, 2, 1, 1]
            approval_weights = [55, 25, 20]   # souvent approuvé
            reason_weights = [5, 30, 8, 12, 38, 7]  # maintenance et déploiement

        random_envs   = [random.choices(ALL_ENVS, weights=env_weights, k=1)[0]]
        if random.random() < 0.3:
            second = random.choices(ALL_ENVS, weights=env_weights, k=1)[0]
            if second != random_envs[0]:
                random_envs.append(second)

        random_access = [random.choices(ALL_ACCESS, weights=access_weights, k=1)[0]]
        if random.random() < 0.2:
            second = random.choices(ALL_ACCESS, weights=access_weights, k=1)[0]
            if second != random_access[0]:
                random_access.append(second)

        request_reason  = random.choices(BANKING_REASONS, weights=reason_weights, k=1)[0]
        approval_status = random.choices(["approved", "pending", "none"], weights=approval_weights, k=1)[0]

        # criticite dérivée — junior en PRD avec accès dangereux = toujours critique
        env_principal = random_envs[0]
        acc_principal = random_access[0]
        if user_seniority == "junior" and env_principal == "PRD" and acc_principal in ["DELETE", "FULL_ACCESS", "DBA_ACCESS"]:
            criticite = "CRITIQUE"
        elif application in ["T24", "MUREX", "SWIFT"] or env_principal == "PRD":
            criticite = random.choices(["SENSITIVE", "CRITIQUE"], weights=[50, 50], k=1)[0]
        elif user_seniority == "senior":
            criticite = random.choices(["BASE", "SENSITIVE"], weights=[80, 20], k=1)[0]
        else:
            criticite = random.choices(["BASE", "SENSITIVE"], weights=[55, 45], k=1)[0]

        # Description naturelle selon le profil
        seniority_label = "Junior" if user_seniority == "junior" else "Senior"
        new_ticket = self.ticket_repo.create({
            "ref": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
            "status": TicketStatus.NEW,
            "employee_id": employee_id,
            "employee_name": random_name,
            "employee_email": employee_email,
            "team_name": random_team,
            "role": random_role,
            "description": (
                f"[{seniority_label}] {random_name} ({random_team}/{random_role}) "
                f"demande un acces [{', '.join(random_access)}] sur [{application}] "
                f"en environnement [{', '.join(random_envs)}] — Motif: {request_reason}"
            ),
            "requested_environments": random_envs,
            "requested_access_details": {
                "access_types":             random_access,
                "application":              application,
                "resource":                 resource,
                "criticite":                criticite,
                "user_seniority":           user_seniority,
                "request_reason":           request_reason,
                "manager_approval_status":  approval_status,
                "justification":            f"Simulation bancaire — profil {seniority_label}",
            },
        })

        # Classification IA automatique
        ai_result = ai_service.classify_and_save(self.db, new_ticket)

        return {
            "message": "Ticket simule cree avec succes",
            "ticket": {
                "id":            new_ticket.id,
                "ref":           new_ticket.ref,
                "employee_name": new_ticket.employee_name,
                "team":          new_ticket.team_name,
                "role":          new_ticket.role,
                "seniority":     user_seniority,
                "application":   application,
                "environments":  new_ticket.requested_environments,
                "access":        new_ticket.requested_access_details,
                "ai_classification": {
                    "level":         ai_result["classification"]["level"],
                    "confidence":    ai_result["classification"]["confidence"],
                    "probabilities": ai_result["classification"].get("probabilities", {}),
                    "assigned_to":   new_ticket.assigned_to,
                },
            },
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