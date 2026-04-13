# app/services/user_service.py

from sqlalchemy.orm import Session
from typing import List, Optional
from app.repositories.user_repository import UserRepository
from app.models.user import DashboardUser, Role
from app.core.exceptions import NotFoundException, ForbiddenException, BusinessException

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_all_admins(self) -> List[DashboardUser]:
        """Récupère tous les administrateurs"""
        return self.user_repo.get_admins()

    def get_admin_by_id(self, admin_id: int) -> DashboardUser:
        """Récupère un administrateur par son ID"""
        admin = self.user_repo.get_by_id(admin_id)
        if not admin:
            raise NotFoundException("Administrateur")
        return admin

    def get_by_username(self, username: str) -> Optional[DashboardUser]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return self.user_repo.get_by_username(username)

    def update_admin(self, admin_id: int, full_name: str = None, email: str = None, role: str = None) -> DashboardUser:
        """Met à jour un administrateur"""
        admin = self.get_admin_by_id(admin_id)
        update_data = {}
        if full_name:
            update_data["fullName"] = full_name
        if email:
            update_data["email"] = email
        if role:
            update_data["role"] = Role(role)
        return self.user_repo.update(admin_id, update_data)

    def toggle_admin_status(self, admin_id: int, is_active: bool, current_user: DashboardUser) -> DashboardUser:
        """Active ou désactive un administrateur"""
        admin = self.get_admin_by_id(admin_id)

        if admin.id == current_user.id and not is_active:
            raise BusinessException("Vous ne pouvez pas désactiver votre propre compte")

        if admin.role == Role.SUPER_ADMIN and admin.id != current_user.id and not is_active:
            raise ForbiddenException("Vous ne pouvez pas désactiver un autre Super Admin")

        return self.user_repo.toggle_active(admin_id, is_active)

    def get_current_user_info(self, user: DashboardUser) -> dict:
        """Retourne les informations de l'utilisateur connecté"""
        return {
            "fullName": user.fullName,
            "email": user.email,
            "role": user.role.value,
            "createdAt": user.createdAt,
            "lastLogin": user.lastLogin,
            "lastLoginIP": user.lastLoginIP,
            "lastSessionDuration": user.lastSessionDuration,
            "profile_image": user.profile_image
        }

    def update_profile(self, user_id: int, first_name: str = None, last_name: str = None, email: str = None) -> DashboardUser:
        """Met à jour le profil utilisateur"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur")

        update_data = {}
        if first_name and last_name:
            update_data["fullName"] = f"{first_name} {last_name}"
        if email:
            existing = self.user_repo.get_by_email(email)
            if existing and existing.id != user_id:
                raise BusinessException("Email déjà utilisé")
            update_data["email"] = email

        return self.user_repo.update(user_id, update_data)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> DashboardUser:
        """Change le mot de passe de l'utilisateur"""
        from app.core.security import verify_password, get_password_hash

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Utilisateur")

        if not verify_password(old_password, user.passwordHash):
            raise BusinessException("Ancien mot de passe incorrect")

        return self.user_repo.update(user_id, {"passwordHash": get_password_hash(new_password)})

    def update_last_login(self, user_id: int, ip: str) -> Optional[DashboardUser]:
        """Met à jour la dernière connexion"""
        return self.user_repo.update_last_login(user_id, ip)

    def update_refresh_token(self, user_id: int, refresh_token: str) -> Optional[DashboardUser]:
        """Met à jour le refresh token"""
        return self.user_repo.update_refresh_token(user_id, refresh_token)

    def clear_refresh_token(self, user_id: int) -> Optional[DashboardUser]:
        """Supprime le refresh token"""
        return self.user_repo.clear_refresh_token(user_id)