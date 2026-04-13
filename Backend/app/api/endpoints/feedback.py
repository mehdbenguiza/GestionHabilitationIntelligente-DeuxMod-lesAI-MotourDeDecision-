# app/api/endpoints/feedback.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.ai_feedback import AIFeedback, AICorrection, compute_profile_signature
from app.models.classification_result import ClassificationResult
from app.models.ticket import Ticket

router = APIRouter(prefix="/feedback", tags=["Feedback IA"])


# ─────────────────────────────────────────────────────────────────────────────
# Schémas
# ─────────────────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    classification_vote: str                     # "like" | "dislike"
    reason_vote: Optional[str] = None            # "like" | "dislike"
    corrected_level: Optional[str] = None        # required si classification_vote == "dislike"
    corrected_reason: Optional[str] = None       # explication humaine (Super Admin)


# ─────────────────────────────────────────────────────────────────────────────
# POST /feedback/{ticket_id}  — Soumettre un vote
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{ticket_id}")
async def submit_feedback(
    ticket_id: int,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """
    Soumet un vote (like / dislike) sur la classification IA d'un ticket.

    Si classification_vote == "dislike" ET corrected_level est fourni :
      → une entrée est créée/mise à jour dans `ai_corrections`
      → la prochaine fois qu'un ticket similaire est classifié, 
        la correction est appliquée automatiquement.
    
    corrected_reason est obligatoire pour un dislike (Super Admin).
    """
    # Vérifier que le ticket existe
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket introuvable")

    # Validation
    vote = body.classification_vote.lower()
    if vote not in ("like", "dislike"):
        raise HTTPException(status_code=422, detail="classification_vote doit être 'like' ou 'dislike'")

    if vote == "dislike":
        if not body.corrected_level:
            raise HTTPException(status_code=422, detail="corrected_level obligatoire en cas de dislike")
        if body.corrected_level not in ("BASE", "SENSITIVE", "CRITICAL"):
            raise HTTPException(status_code=422, detail="corrected_level invalide")
        if current_user.role.value == "SUPER_ADMIN" and not body.corrected_reason:
            raise HTTPException(status_code=422, detail="corrected_reason obligatoire pour un Super Admin")

    # Récupérer la dernière classification du ticket
    classification = (
        db.query(ClassificationResult)
        .filter(ClassificationResult.ticket_id == ticket_id)
        .order_by(ClassificationResult.processed_at.desc())
        .first()
    )

    # Éviter les doublons (un reviewer ne vote qu'une fois par ticket)
    existing = (
        db.query(AIFeedback)
        .filter(AIFeedback.ticket_id == ticket_id, AIFeedback.reviewer == current_user.username)
        .first()
    )
    if existing:
        # Mise à jour du vote existant
        existing.classification_vote = vote
        existing.reason_vote         = body.reason_vote
        existing.corrected_level     = body.corrected_level
        existing.corrected_reason    = body.corrected_reason
        feedback = existing
    else:
        feedback = AIFeedback(
            ticket_id           = ticket_id,
            classification_id   = classification.id if classification else None,
            reviewer            = current_user.username,
            classification_vote = vote,
            reason_vote         = body.reason_vote,
            corrected_level     = body.corrected_level,
            corrected_reason    = body.corrected_reason,
        )
        db.add(feedback)

    if vote == "like":
        body.corrected_level = classification.predicted_level if classification else "BASE"
        body.corrected_reason = "Classification validée par un Admin/SuperAdmin (Like)"

    # ── Propagation automatique de la correction ──────────────────────────
    if (vote == "dislike" and body.corrected_level and body.corrected_reason) or (vote == "like"):
        details     = ticket.requested_access_details or {}
        envs        = ticket.requested_environments or []
        application = details.get("application", "E_BANKING")
        environment = envs[0] if envs else "DEV2"
        access_type = (details.get("access_types") or ["READ"])[0]
        team        = ticket.team_name or "MOE"
        resource    = details.get("resource", "OTHER")

        sig = compute_profile_signature(application, environment, access_type, team, resource)

        existing_corr = db.query(AICorrection).filter(AICorrection.profile_signature == sig).first()
        if existing_corr:
            # Mise à jour de la correction existante avec la nouvelle
            existing_corr.corrected_level  = body.corrected_level
            existing_corr.corrected_reason = body.corrected_reason
            existing_corr.reviewer         = current_user.username
            existing_corr.source_ticket_id = ticket_id
        else:
            correction = AICorrection(
                profile_signature = sig,
                application       = application,
                environment       = environment,
                access_type       = access_type,
                team              = team,
                resource          = resource,
                corrected_level   = body.corrected_level,
                corrected_reason  = body.corrected_reason,
                source_ticket_id  = ticket_id,
                reviewer          = current_user.username,
                usage_count       = 0,
            )
            db.add(correction)

        print(f"✅ Correction enregistrée : {team}/{application}/{environment}/{access_type} → {body.corrected_level}")

    db.commit()

    return {
        "message": "Feedback enregistré avec succès",
        "ticket_id": ticket_id,
        "vote": vote,
        "correction_propagated": (vote == "dislike" and bool(body.corrected_reason)) or vote == "like",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /feedback/{ticket_id}  — Feedback déjà soumis pour un ticket
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ticket_id}")
async def get_feedback(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Retourne le feedback de l'utilisateur courant pour un ticket donné."""
    feedback = (
        db.query(AIFeedback)
        .filter(AIFeedback.ticket_id == ticket_id, AIFeedback.reviewer == current_user.username)
        .first()
    )
    if not feedback:
        return {"has_feedback": False}
    return {
        "has_feedback":         True,
        "classification_vote":  feedback.classification_vote,
        "reason_vote":          feedback.reason_vote,
        "corrected_level":      feedback.corrected_level,
        "corrected_reason":     feedback.corrected_reason,
        "created_at":           feedback.created_at.isoformat() if feedback.created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /feedback/stats  — Statistiques globales des votes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats/summary")
async def feedback_stats(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Stats globales : taux de satisfaction, nombre de corrections."""
    from sqlalchemy import func

    total   = db.query(AIFeedback).count()
    likes   = db.query(AIFeedback).filter(AIFeedback.classification_vote == "like").count()
    dislikes= db.query(AIFeedback).filter(AIFeedback.classification_vote == "dislike").count()
    corrections = db.query(AICorrection).count()
    corr_used   = db.query(func.sum(AICorrection.usage_count)).scalar() or 0

    return {
        "total_votes":       total,
        "likes":             likes,
        "dislikes":          dislikes,
        "satisfaction_rate": round((likes / total * 100), 1) if total > 0 else 0,
        "corrections_count": corrections,
        "corrections_applied": corr_used,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /feedback/corrections  — Bibliothèque de corrections (Super Admin)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/corrections/list")
async def list_corrections(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Liste toutes les corrections actives dans la bibliothèque (Super Admin)."""
    if current_user.role.value not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(status_code=403, detail="Accès réservé aux Admins")

    corrections = db.query(AICorrection).order_by(AICorrection.usage_count.desc()).all()
    return [
        {
            "id":               c.id,
            "application":      c.application,
            "environment":      c.environment,
            "access_type":      c.access_type,
            "team":             c.team,
            "resource":         c.resource,
            "corrected_level":  c.corrected_level,
            "corrected_reason": c.corrected_reason,
            "reviewer":         c.reviewer,
            "usage_count":      c.usage_count,
            "created_at":       c.created_at.isoformat() if c.created_at else None,
            "last_used_at":     c.last_used_at.isoformat() if c.last_used_at else None,
        }
        for c in corrections
    ]


@router.delete("/corrections/{correction_id}")
async def delete_correction(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Supprime une correction (Super Admin uniquement)."""
    if current_user.role.value != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Réservé aux Super Admins")
    c = db.query(AICorrection).filter(AICorrection.id == correction_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Correction introuvable")
    db.delete(c)
    db.commit()
    return {"message": "Correction supprimée"}
