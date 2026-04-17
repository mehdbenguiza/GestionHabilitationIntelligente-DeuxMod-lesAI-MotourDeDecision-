# app/services/audit_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any, Dict
from app.models.audit_log import AuditLog
from app.models.login_history import LoginHistory
from app.models.notification import Notification
from app.models.user import DashboardUser

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        ticket_id: Optional[int],
        ticket_ref: Optional[str],
        acteur_name: str,
        acteur_role: str,
        action: str,
        resultat: str = "Succès",
        environnement: str = "Inconnu",
        niveau_acces: str = "Inconnu",
        details: Optional[Dict[str, Any]] = None,
        categorie: str = "ACTION"
    ):
        """Standard log for ticket-related actions."""
        audit = AuditLog(
            ticket_id=ticket_id,
            ticket_ref=ticket_ref,
            acteur_name=acteur_name,
            acteur_role=acteur_role,
            action=action,
            categorie=categorie,
            resultat=resultat,
            environnement=environnement,
            niveau_acces=niveau_acces,
            details=details or {}
        )
        db.add(audit)
        # We don't commit here to allow atomic operations in calling services
        return audit

    @staticmethod
    def log_security(
        db: Session,
        user_id: int,
        action: str,
        ip_address: str = "127.0.0.1",
        details: str = ""
    ):
        """Standard log for user security (Login, Profile update, etc.)."""
        history = LoginHistory(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(history)
        return history

    @staticmethod
    def notify(
        db: Session,
        title: str,
        message: str,
        type: str = "info",
        target_roles: str = "ADMIN,SUPER_ADMIN"
    ):
        """Standard system notification."""
        notif = Notification(
            title=title,
            message=message,
            type=type,
            target_roles=target_roles,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        return notif

audit_service = AuditService()
