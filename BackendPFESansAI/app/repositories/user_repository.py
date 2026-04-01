# app/repositories/user_repository.py

from sqlalchemy.orm import Session
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.user import DashboardUser, Role
from datetime import datetime

class UserRepository(BaseRepository[DashboardUser]):
    def __init__(self, db: Session):
        super().__init__(db, DashboardUser)

    def get_by_username(self, username: str) -> Optional[DashboardUser]:
        return self.db.query(DashboardUser).filter(DashboardUser.username == username).first()

    def get_by_email(self, email: str) -> Optional[DashboardUser]:
        return self.db.query(DashboardUser).filter(DashboardUser.email == email).first()

    def get_admins(self) -> List[DashboardUser]:
        return self.db.query(DashboardUser).filter(
            DashboardUser.role.in_([Role.ADMIN, Role.SUPER_ADMIN])
        ).all()

    def get_super_admins(self) -> List[DashboardUser]:
        return self.db.query(DashboardUser).filter(DashboardUser.role == Role.SUPER_ADMIN).all()

    def get_active_admins(self) -> List[DashboardUser]:
        return self.db.query(DashboardUser).filter(
            DashboardUser.role.in_([Role.ADMIN, Role.SUPER_ADMIN]),
            DashboardUser.isActive == True
        ).all()

    def update_last_login(self, user_id: int, ip: str) -> Optional[DashboardUser]:
        return self.update(user_id, {
            "lastLogin": datetime.utcnow(),
            "lastLoginIP": ip
        })

    def toggle_active(self, user_id: int, is_active: bool) -> Optional[DashboardUser]:
        return self.update(user_id, {"isActive": is_active})

    def update_refresh_token(self, user_id: int, refresh_token: str) -> Optional[DashboardUser]:
        return self.update(user_id, {
            "refresh_token": refresh_token,
            "refresh_token_created_at": datetime.utcnow()
        })

    def clear_refresh_token(self, user_id: int) -> Optional[DashboardUser]:
        return self.update(user_id, {
            "refresh_token": None,
            "refresh_token_created_at": None
        })

    def get_by_role(self, role: Role) -> List[DashboardUser]:
        return self.db.query(DashboardUser).filter(DashboardUser.role == role).all()