# app/api/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import DashboardUser
from app.models.login_history import LoginHistory
from app.core.dependencies import require_super_admin, get_current_user
from app.services.user_service import UserService
from app.schemas.user import UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/admins")
def get_admins(
    user_service: UserService = Depends(get_user_service),
    current_user: DashboardUser = Depends(require_super_admin)
):
    """Liste tous les administrateurs (Super Admin uniquement)"""
    admins = user_service.get_all_admins()
    return [
        {
            "id": admin.id,
            "username": admin.username,
            "fullName": admin.fullName,
            "email": admin.email,
            "role": admin.role.value,
            "isActive": admin.isActive,
            "lastLogin": admin.lastLogin,
            "createdAt": admin.createdAt
        }
        for admin in admins
    ]


@router.put("/admins/{admin_id}")
def update_admin(
    admin_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: DashboardUser = Depends(require_super_admin)
):
    """Modifie un administrateur (Super Admin uniquement)"""
    admin = user_service.update_admin(
        admin_id,
        full_name=user_data.fullName,
        email=user_data.email,
        role=user_data.role
    )
    return {"msg": "Administrateur modifié avec succès"}


@router.patch("/admins/{admin_id}/status")
def toggle_admin_status(
    admin_id: int,
    status_data: dict,
    user_service: UserService = Depends(get_user_service),
    current_user: DashboardUser = Depends(require_super_admin)
):
    """Active ou désactive un administrateur (Super Admin uniquement)"""
    admin = user_service.toggle_admin_status(
        admin_id,
        status_data.get("isActive", True),
        current_user
    )
    return {"msg": f"Administrateur {'activé' if admin.isActive else 'désactivé'} avec succès"}


@router.get("/me")
def get_current_user_info(
    current_user: DashboardUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Informations de l'utilisateur connecté"""
    return user_service.get_current_user_info(current_user)


@router.get("/login-history")
def get_login_history(
    limit: int = 10,
    current_user: DashboardUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique des connexions de l'utilisateur"""
    history = db.query(LoginHistory)\
        .filter(LoginHistory.user_id == current_user.id)\
        .order_by(LoginHistory.timestamp.desc())\
        .limit(limit)\
        .all()
    return [
        {
            "id": str(h.id),
            "action": h.action,
            "date": h.timestamp,
            "ip": h.ip_address,
            "details": h.details
        }
        for h in history
    ]


@router.put("/profile")
def update_profile(
    profile_data: dict,
    current_user: DashboardUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db)
):
    """Met à jour le profil utilisateur"""
    admin = user_service.update_profile(
        current_user.id,
        first_name=profile_data.get("firstName"),
        last_name=profile_data.get("lastName"),
        email=profile_data.get("email")
    )

    login_history = LoginHistory(
        user_id=current_user.id,
        action="Modification du profil",
        ip_address="127.0.0.1",
        details="Informations personnelles mises à jour"
    )
    db.add(login_history)
    db.commit()

    return {"msg": "Profil mis à jour avec succès"}


@router.post("/change-password")
def change_password(
    password_data: dict,
    current_user: DashboardUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db)
):
    """Change le mot de passe de l'utilisateur"""
    user_service.change_password(
        current_user.id,
        password_data["oldPassword"],
        password_data["newPassword"]
    )

    login_history = LoginHistory(
        user_id=current_user.id,
        action="Changement de mot de passe",
        ip_address="127.0.0.1",
        details="Mot de passe modifié"
    )
    db.add(login_history)
    db.commit()

    return {"msg": "Mot de passe changé avec succès"}