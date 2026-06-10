from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

# Durée des tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7      # 7 jours

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    try:
        if not plain_password or not hashed_password:
            return False
        
        # Encoding to bytes
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Truncate plain_bytes to 72 bytes (bcrypt limit) to prevent ValueError in newer bcrypt versions
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
            
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"❌ Erreur verify: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Génère un hash de mot de passe"""
    try:
        if not password:
            return ""
            
        # Encoding to bytes
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"❌ Erreur hash: {e}")
        raise e

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un access token (court)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un refresh token (long) pour la session persistante"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Décode et vérifie un token"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Vérifie un token et son type"""
    payload = decode_token(token)
    if payload and payload.get("type") == token_type:
        return payload
    return None