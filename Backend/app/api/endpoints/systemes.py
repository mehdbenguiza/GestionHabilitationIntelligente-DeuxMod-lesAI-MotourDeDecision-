# app/api/endpoints/systemes.py
"""
Endpoints REST pour le référentiel des Systèmes d'Information BIAT.
Permet de consulter les systèmes disponibles et les profils actifs par système.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.systeme import Systeme
from app.models.access_profile import AccessProfile, ProfileStatus

router = APIRouter(prefix="/systemes", tags=["Systèmes"])


def serialize_systeme(s: Systeme) -> dict:
    return {
        "id":               s.id,
        "code":             s.code,
        "nom":              s.nom,
        "description":      s.description,
        "applications":     s.applications or [],
        "environments":     s.environments or [],
        "sensibilite":      s.sensibilite,
        "responsable_email":s.responsable_email,
        "actif":            s.actif,
        "created_at":       s.created_at.isoformat() if s.created_at else None,
    }


@router.get("", response_model=None)
def list_systemes(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Liste tous les systèmes d'information actifs."""
    systemes = db.query(Systeme).filter(Systeme.actif == True).order_by(Systeme.nom).all()
    return [serialize_systeme(s) for s in systemes]


@router.get("/{system_id}", response_model=None)
def get_systeme(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Détail d'un système + statistiques de profils actifs."""
    systeme = db.query(Systeme).filter(Systeme.id == system_id).first()
    if not systeme:
        raise HTTPException(status_code=404, detail="Système introuvable")

    total_profiles = db.query(AccessProfile).filter(AccessProfile.system_id == system_id).count()
    active_profiles= db.query(AccessProfile).filter(
        AccessProfile.system_id == system_id,
        AccessProfile.status == ProfileStatus.ACTIVE
    ).count()

    data = serialize_systeme(systeme)
    data["stats"] = {
        "total_profiles":  total_profiles,
        "active_profiles": active_profiles,
        "revoked_profiles":total_profiles - active_profiles,
    }
    return data


@router.get("/{system_id}/profiles", response_model=None)
def list_systeme_profiles(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Liste des profils d'accès actifs sur un système donné."""
    systeme = db.query(Systeme).filter(Systeme.id == system_id).first()
    if not systeme:
        raise HTTPException(status_code=404, detail="Système introuvable")

    profiles = db.query(AccessProfile).filter(
        AccessProfile.system_id == system_id,
        AccessProfile.status == ProfileStatus.ACTIVE,
    ).order_by(AccessProfile.created_at.desc()).all()

    return {
        "systeme": systeme.nom,
        "total":   len(profiles),
        "profiles": [
            {
                "id":           p.id,
                "account_name": p.account_name,
                "employee_id":  p.employee_id,
                "application":  p.application,
                "environments": p.environments,
                "access_types": p.access_types,
                "status":       p.status.value,
                "created_at":   p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
    }
