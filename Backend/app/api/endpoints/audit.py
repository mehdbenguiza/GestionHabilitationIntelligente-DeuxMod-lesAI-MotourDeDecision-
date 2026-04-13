from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.audit_log import AuditLog
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/")
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user)
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    # Sérialisation intelligente pour le Frontend
    result = []
    for log in logs:
        # Mapping des rôles techniques vers rôles Frontend
        role_map = {
            "AI_ENGINE": "IA",
            "ADMIN": "Admin",
            "SUPER_ADMIN": "Super Admin"
        }
        frontend_role = role_map.get(log.acteur_role, log.acteur_role)

        result.append({
            "id": f"LOG-{log.id:04d}",
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "acteur": log.acteur_name,
            "role": frontend_role,
            "action": log.action,
            "categorie": log.categorie if log.categorie != "AI_AUDIT" else "Sécurité",
            "ticketRef": log.ticket_ref,
            "environnement": log.environnement,
            "resultat": log.resultat,
            "niveauAcces": log.niveau_acces,
            "details": log.details or {}
        })
    return result
