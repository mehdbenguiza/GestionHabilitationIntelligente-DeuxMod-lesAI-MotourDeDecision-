# app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import DashboardUser, Role
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=True
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Récupère l'utilisateur courant à partir du token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")

        if username is None:
            raise credentials_exception

        # Vérifier que c'est bien un access token (pas un refresh token)
        if token_type != "access":
            raise credentials_exception

    except JWTError as e:
        print(f"❌ Erreur JWT: {e}")
        raise credentials_exception

    # Récupérer l'utilisateur en base
    user = db.query(DashboardUser).filter(DashboardUser.username == username).first()
    
    if user is None:
        raise credentials_exception

    if not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez votre administrateur."
        )

    return user


def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Version optionnelle - retourne None si non authentifié
    """
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


def require_super_admin(current_user: DashboardUser = Depends(get_current_user)):
    """
    Vérifie que l'utilisateur est un Super Admin
    """
    if current_user.role != Role.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le Super Admin peut effectuer cette action"
        )
    return current_user


def require_admin(current_user: DashboardUser = Depends(get_current_user)):
    """
    Vérifie que l'utilisateur est au moins Admin (Admin ou Super Admin)
    """
    if current_user.role not in [Role.ADMIN, Role.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user