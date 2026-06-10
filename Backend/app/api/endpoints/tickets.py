# app/api/endpoints/tickets.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.services.ticket_service import TicketService
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.ticket import TicketStatus
from app.schemas.ticket import TicketResponse
from app.services.mfa_service import mfa_service
from app.services.queue_service import ai_queue

router = APIRouter(prefix="/tickets", tags=["tickets"])


class ApproveRequest(BaseModel):
    resolution: Optional[str] = "Demande approvée"
    mfa_code:   Optional[str] = None   # Obligatoire pour tickets CRITIQUE


def get_ticket_service(db: Session = Depends(get_db)) -> TicketService:
    return TicketService(db)


@router.get("/sync")
async def sync_tickets(
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Synchronise les tickets depuis iTop"""
    return ticket_service.sync_from_itop()


@router.get("", response_model=List[TicketResponse])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    team: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Liste des tickets avec filtres optionnels — inclut les données IA"""
    return ticket_service.get_all_tickets(status, team, skip, limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Détail d'un ticket — inclut les données IA"""
    return ticket_service.get_ticket_by_id(ticket_id)


@router.post("/{ticket_id}/approve")
async def approve_ticket(
    ticket_id: int,
    body: ApproveRequest = ApproveRequest(),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Approuver un ticket.
    Pour les tickets CRITIQUE : le code MFA est requis.
    Appeler d'abord POST /tickets/{id}/request-mfa pour obtenir le code.
    """
    from app.models.ticket import Ticket
    from app.database import get_db as _get_db
    from app.models.classification_result import ClassificationResult

    # Lire le ticket pour vérifier s'il est CRITIQUE
    db = ticket_service.db
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    # Déterminer le niveau IA
    cls_result = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.ticket_id == ticket_id)
        .order_by(ClassificationResult.processed_at.desc())
        .first()
    )
    ai_level   = cls_result.predicted_level if cls_result else "BASE"
    risk_score = cls_result.risk_score_rules if cls_result else 0

    # V3.0 : Vérifier MFA si ticket CRITIQUE
    if mfa_service.is_mfa_required(ai_level, risk_score):
        if not body.mfa_code:
            raise HTTPException(
                status_code=428,
                detail={
                    "error": "MFA_REQUIRED",
                    "message": "Ce ticket est CRITIQUE. Un code MFA est requis avant approbation.",
                    "action": f"Appelez POST /tickets/{ticket_id}/request-mfa pour recevoir votre code."
                }
            )
        mfa_result = mfa_service.verify_code(ticket_id, current_user.username, body.mfa_code)
        if not mfa_result["valid"]:
            raise HTTPException(
                status_code=401,
                detail={"error": "MFA_INVALID", "message": mfa_result["reason"]}
            )

    result_ticket = ticket_service.approve_ticket(ticket_id, current_user, body.resolution)
    return {
        "message": "Ticket approuvé",
        "ticket_id": result_ticket.id,
        "mfa_verified": mfa_service.is_mfa_required(ai_level, risk_score),
        "ticket": result_ticket
    }


@router.post("/{ticket_id}/reject")
async def reject_ticket(
    ticket_id: int,
    reason: str = Query(..., description="Motif du rejet (obligatoire)"),
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """Rejeter un ticket avec motif obligatoire"""
    ticket = ticket_service.reject_ticket(ticket_id, reason, current_user)
    return {"message": "Ticket rejeté", "ticket_id": ticket.id, "reason": reason, "ticket": ticket}


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
        "ticket": ticket
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


# ==================== ENDPOINTS MFA V3.0 ====================

@router.post("/{ticket_id}/request-mfa")
async def request_mfa_code(
    ticket_id: int,
    ticket_service: TicketService = Depends(get_ticket_service),
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Génère un code MFA (6 chiffres, 5 min) pour l'approbation d'un ticket CRITIQUE.
    Le code est affiché dans la console (simulation SMS/Email).
    """
    from app.models.ticket import Ticket
    from app.models.classification_result import ClassificationResult
    from app.services.email_service import send_email, _html_base

    db = ticket_service.db
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    cls_result = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.ticket_id == ticket_id)
        .order_by(ClassificationResult.processed_at.desc())
        .first()
    )
    ai_level   = cls_result.predicted_level if cls_result else "BASE"
    risk_score = cls_result.risk_score_rules if cls_result else 0

    if not mfa_service.is_mfa_required(ai_level, risk_score):
        return {
            "mfa_required": False,
            "message": "Ce ticket ne nécessite pas de MFA (niveau non critique)."
        }

    code = mfa_service.generate_code(ticket_id, current_user.username)
    
    # Envoi par email
    admin_email = current_user.email if hasattr(current_user, 'email') and current_user.email else "benguizamehdi3@gmail.com"
    subject = f"[BIAT Sécurité] Code d'authentification requis pour Ticket #{ticket.ref}"
    content = f"""
    <div style="background:#fefce8;border:1px solid #fef08a;border-radius:8px;padding:16px 20px;margin-bottom:28px;">
      <span style="font-size:28px;margin-right:12px;">🛡️</span>
      <div style="display:inline-block;vertical-align:middle;">
        <div style="color:#854d0e;font-size:16px;font-weight:700;">Action Critique Détectée</div>
        <div style="color:#a16207;font-size:13px;margin-top:2px;">Ticket N° <strong>{ticket.ref}</strong></div>
      </div>
    </div>
    <p style="color:#1e293b;font-size:15px;line-height:1.7;margin:0 0 24px 0;">
      Bonjour <strong>{current_user.username}</strong>,<br/><br/>
      Vous tentez d'approuver une habilitation jugée <strong style="color:#b91c1c;">CRITIQUE</strong>. Veuillez saisir le code de sécurité ci-dessous dans l'interface pour confirmer l'action.
    </p>
    <div style="text-align:center;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:24px;margin-bottom:24px;">
      <div style="color:#64748b;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Votre Code de Sécurité (Valable 5 minutes)</div>
      <div style="font-size:32px;font-weight:900;letter-spacing:8px;color:#003087;">{code}</div>
    </div>
    """
    html_body = _html_base(content, subject)
    send_email(to_address=admin_email, subject=subject, html_body=html_body)

    return {
        "mfa_required": True,
        "message": f"Code MFA généré pour le ticket #{ticket_id} (CRITIQUE).",
        "hint":    f"Le code à 6 chiffres a été envoyé par e-mail à l'administrateur ({admin_email}).",
        "expires_in": "5 minutes",
        "dev_code": code,
    }


# ==================== QUEUE STATUS V3.0 ====================

@router.get("/queue/status", include_in_schema=True)
async def ai_queue_status(
    current_user: DashboardUser = Depends(get_current_user)
):
    """Statut de la file d'attente IA (Architecture Micro-services simulée)."""
    return ai_queue.get_status()