# app/api/endpoints/profiles.py
"""
Endpoints REST pour la gestion des profils d'accès.
Les profils sont créés automatiquement lors de l'approbation d'un ticket.
Les admins peuvent les consulter, filtrer et révoquer.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.access_profile import AccessProfile, ProfileStatus
from app.services.profile_service import profile_service

router = APIRouter(prefix="/profiles", tags=["Profils d'accès"])


def serialize_profile(p: AccessProfile) -> dict:
    return {
        "id":              p.id,
        "ticket_id":       p.ticket_id,
        "employee_id":     p.employee_id,
        "system_id":       p.system_id,
        "system_name":     p.systeme.nom if p.systeme else None,
        "account_name":    p.account_name,
        # Le mot de passe en clair n'est JAMAIS renvoyé par l'API
        "password_hash":   "***hidden***",
        "temp_password_cleared": p.temp_password_cleared,
        "application":     p.application,
        "environments":    p.environments  or [],
        "access_types":    p.access_types  or [],
        "resource":        p.resource,
        "status":          p.status.value,
        "created_by":      p.created_by,
        "revoked_by":      p.revoked_by,
        "revoked_reason":  p.revoked_reason,
        "created_at":      p.created_at.isoformat()  if p.created_at  else None,
        "revoked_at":      p.revoked_at.isoformat()  if p.revoked_at  else None,
        "expires_at":      p.expires_at.isoformat()  if p.expires_at  else None,
        "notification_sent":     p.notification_sent,
        "notification_sent_at":  p.notification_sent_at.isoformat() if p.notification_sent_at else None,
        # Infos de l'employé dénormalisées depuis la relation ticket
        "employee_name":   p.ticket.employee_name   if p.ticket else None,
        "employee_email":  p.ticket.employee_email  if p.ticket else None,
        "team_name":       p.ticket.team_name       if p.ticket else None,
        "ticket_ref":      p.ticket.ref             if p.ticket else None,
    }


@router.get("", response_model=None)
def list_profiles(
    status: Optional[str] = Query(None, description="ACTIVE | REVOKED | EXPIRED"),
    application: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """
    Liste les profils d'accès avec filtres optionnels.
    Le mot de passe n'est jamais exposé.
    """
    query = db.query(AccessProfile)

    if status:
        try:
            status_enum = ProfileStatus(status.upper())
            query = query.filter(AccessProfile.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide : {status}. Valeurs : ACTIVE, REVOKED, EXPIRED")

    if application:
        query = query.filter(AccessProfile.application == application.upper())

    profiles = query.order_by(AccessProfile.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total":    query.count(),
        "skip":     skip,
        "limit":    limit,
        "profiles": [serialize_profile(p) for p in profiles],
    }


@router.get("/{profile_id}", response_model=None)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Détail complet d'un profil d'accès."""
    p = db.query(AccessProfile).filter(AccessProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    return serialize_profile(p)


@router.post("/{profile_id}/revoke", response_model=None)
def revoke_profile(
    profile_id: int,
    reason: str = Query(..., description="Motif de révocation (obligatoire)"),
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """
    Révoque un profil d'accès actif.
    Réservé aux ADMIN et SUPER_ADMIN.
    """
    if current_user.role.value not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Le motif de révocation est obligatoire")

    try:
        profile = profile_service.revoke_profile(
            db         = db,
            profile_id = profile_id,
            revoked_by = current_user.fullName or current_user.username,
            reason     = reason,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message":    f"Profil '{profile.account_name}' révoqué avec succès",
        "profile_id": profile.id,
        "status":     profile.status.value,
        "revoked_by": profile.revoked_by,
        "revoked_at": profile.revoked_at.isoformat() if profile.revoked_at else None,
    }

@router.post("/{profile_id}/reactivate", response_model=None)
def reactivate_profile_endpoint(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """
    Réactive un profil d'accès révoqué.
    Réservé aux ADMIN et SUPER_ADMIN.
    """
    if current_user.role.value not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    try:
        profile = profile_service.reactivate_profile(
            db         = db,
            profile_id = profile_id,
            reactivated_by = current_user.fullName or current_user.username,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message":    f"Profil '{profile.account_name}' réactivé avec succès",
        "profile_id": profile.id,
        "status":     profile.status.value,
    }


@router.get("/employee/{employee_id}", response_model=None)
def get_employee_profiles(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Retourne tous les profils d'un employé donné (historique complet)."""
    profiles = db.query(AccessProfile).filter(
        AccessProfile.employee_id == employee_id
    ).order_by(AccessProfile.created_at.desc()).all()

    return {
        "employee_id": employee_id,
        "total":       len(profiles),
        "profiles":    [serialize_profile(p) for p in profiles],
    }
