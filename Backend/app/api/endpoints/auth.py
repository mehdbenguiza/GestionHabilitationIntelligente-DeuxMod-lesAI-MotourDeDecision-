from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
import asyncio
from app.database import get_db
from app.models.user import DashboardUser
from app.models.login_history import LoginHistory
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, verify_token, decode_token
)
from app.core.dependencies import require_super_admin, get_current_user
from app.core.email import send_reset_password_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Stockage temporaire des codes OTP
reset_codes = {}

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


@router.post("/login")
def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    print(f"\n🔐 Login: {user_data.username}")
    
    user = db.query(DashboardUser).filter(DashboardUser.username == user_data.username).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    
    password_to_check = user_data.password
    if len(password_to_check) > 72:
        password_to_check = password_to_check[:72]
    
    if not verify_password(password_to_check, user.passwordHash):
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    
    if not user.isActive:
        raise HTTPException(status_code=403, detail="Compte désactivé. Veuillez contacter votre superviseur.")
    
    # Mise à jour dernière connexion
    user.lastLogin = datetime.utcnow()
    user.lastLoginIP = request.client.host if request.client else "127.0.0.1"
    
    # Création des tokens
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Stocker le refresh token en base (pour révocation)
    user.refresh_token = refresh_token
    
    # Notification s'il est admin
    if user.role.value in ["SUPER_ADMIN", "ADMIN"]:
        from app.models.notification import Notification
        display_name = user.fullName if user.fullName else user.username
        role_display = "Super Admin" if user.role.value == "SUPER_ADMIN" else "Admin"
        
        notif = Notification(
            title=f"Connexion: {role_display}",
            message=f"{role_display} {display_name} vient de se connecter au dashboard.",
            type="info",
            target_roles="SUPER_ADMIN"
        )
        db.add(notif)
    
    db.commit()
    
    # ✅ Stocker le refresh token en HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Mettre True en HTTPS
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/auth/refresh"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 15 * 60
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Rafraîchit l'access token via le refresh token en cookie"""
    
    refresh_token_cookie = request.cookies.get("refresh_token")
    
    if not refresh_token_cookie:
        raise HTTPException(status_code=401, detail="Refresh token manquant")
    
    payload = verify_token(refresh_token_cookie, token_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")
    
    username = payload.get("sub")
    
    user = db.query(DashboardUser).filter(DashboardUser.username == username).first()
    if not user or not user.isActive:
        raise HTTPException(status_code=401, detail="Utilisateur invalide")
    
    # Vérifier que le refresh token correspond à celui en base
    if user.refresh_token != refresh_token_cookie:
        raise HTTPException(status_code=401, detail="Refresh token révoqué")
    
    # Créer un nouveau access token
    new_access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 15 * 60
    }


@router.post("/register")
def register(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(require_super_admin)
):
    db_user = db.query(DashboardUser).filter(DashboardUser.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username déjà pris")
    
    db_email = db.query(DashboardUser).filter(DashboardUser.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    hashed = get_password_hash(user.password)
    new_user = DashboardUser(
        username=user.username,
        fullName=user.fullName,
        email=user.email,
        passwordHash=hashed,
        role=user.role,
        isActive=True,
        createdAt=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    login_history = LoginHistory(
        user_id=new_user.id,
        action="Création du compte",
        ip_address="127.0.0.1",
        details=f"Créé par {current_user.username}"
    )
    db.add(login_history)
    db.commit()
    
    return {"msg": f"Utilisateur {user.username} créé avec succès par {current_user.username}"}


@router.post("/logout")
def logout(
    response: Response,
    current_user: DashboardUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculer la durée de la session
    if current_user.lastLogin:
        duration = datetime.utcnow() - current_user.lastLogin
        minutes = int(duration.total_seconds() // 60)
        hours = minutes // 60
        mins = minutes % 60
        duration_str = f"{hours}h {mins}min" if hours > 0 else f"{mins} min"
        current_user.lastSessionDuration = duration_str
    
    # Supprimer le refresh token de la base
    current_user.refresh_token = None
    db.commit()
    
    # Supprimer le cookie
    response.delete_cookie("refresh_token", path="/auth/refresh")
    
    return {"msg": "Déconnexion réussie"}


# ==================== ROUTES DE RÉCUPÉRATION DE MOT DE PASSE ====================

@router.post("/forgot-password/request")
async def request_password_reset(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Étape 1: Demande de réinitialisation de mot de passe
    Envoie un code OTP par email
    """
    try:
        # Récupérer les données du body
        data = await request.json()
        email = data.get("email")
        
        print(f"📧 Demande de reset pour: {email}")
        
        if not email:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email requis"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier si l'email existe
        user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
        
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
        if not user:
            # Simuler un délai pour éviter les attaques par timing
            await asyncio.sleep(1)
            return JSONResponse(
                content={"message": "Si l'email existe, un code de réinitialisation a été envoyé"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Générer un code OTP
        otp_code = generate_otp()
        print(f"🔐 Code généré pour {email}: {otp_code}")
        
        # Stocker le code
        reset_codes[email] = {
            "code": otp_code,
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "attempts": 0,
            "user_id": user.id,
            "verified": False
        }
        
        # Envoyer l'email en arrière-plan
        background_tasks.add_task(
            send_reset_password_email,
            email=email,
            full_name=user.fullName,
            otp_code=otp_code
        )
        
        # Enregistrer dans l'historique
        login_history = LoginHistory(
            user_id=user.id,
            action="Demande de réinitialisation de mot de passe",
            ip_address=request.client.host if request.client else "127.0.0.1",
            details=f"Code envoyé à {email}"
        )
        db.add(login_history)
        db.commit()
        
        return JSONResponse(
            content={"message": "Code de réinitialisation envoyé"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except Exception as e:
        print(f"❌ Erreur dans request_password_reset: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Erreur serveur: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )


@router.post("/forgot-password/verify")
async def verify_reset_code(
    request: Request
):
    """
    Étape 2: Vérification du code OTP
    """
    try:
        # Récupérer les données du body
        data = await request.json()
        email = data.get("email")
        code = data.get("code")
        
        print(f"🔐 Vérification code pour {email}: {code}")
        
        if not email or not code:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email et code requis"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        if email not in reset_codes:
            return JSONResponse(
                status_code=400,
                content={"detail": "Code invalide ou expiré"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        reset_data = reset_codes[email]
        
        # Vérifier l'expiration
        if datetime.utcnow() > reset_data["expires_at"]:
            del reset_codes[email]
            return JSONResponse(
                status_code=400,
                content={"detail": "Code expiré. Veuillez refaire une demande."},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier le nombre de tentatives
        if reset_data["attempts"] >= 5:
            del reset_codes[email]
            return JSONResponse(
                status_code=400,
                content={"detail": "Trop de tentatives. Veuillez refaire une demande."},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier le code
        if reset_data["code"] != code:
            reset_data["attempts"] += 1
            return JSONResponse(
                status_code=400,
                content={"detail": "Code incorrect"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Marquer comme vérifié
        reset_data["verified"] = True
        
        # Générer un token temporaire avec expiration de 15 minutes
        reset_token = create_access_token(
            data={"sub": email, "purpose": "password_reset"},
            expires_delta=timedelta(minutes=15)
        )
        
        return JSONResponse(
            content={
                "message": "Code valide",
                "reset_token": reset_token
            },
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except Exception as e:
        print(f"❌ Erreur dans verify_reset_code: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Erreur serveur: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )


@router.post("/forgot-password/reset")
async def reset_password(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Étape 3: Réinitialisation du mot de passe
    """
    try:
        # Récupérer les données du body
        data = await request.json()
        email = data.get("email")
        new_password = data.get("new_password")
        reset_token = data.get("reset_token")
        
        print(f"🔐 Reset password pour {email}")
        print(f"📏 Longueur originale: {len(new_password) if new_password else 0}")
        
        if not email or not new_password:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email et nouveau mot de passe requis"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # ✅ SOLUTION CRITIQUE: Troncature forcée à 72 caractères
        if len(new_password) > 72:
            print(f"⚠️ Troncature de {len(new_password)} à 72 caractères")
            new_password = new_password[:72]
            print(f"📏 Longueur après troncature: {len(new_password)}")
        
        # Validation de la longueur minimale
        if len(new_password) < 8:
            return JSONResponse(
                status_code=400,
                content={"detail": "Le mot de passe doit contenir au moins 8 caractères"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier que l'email a bien été validé
        if email not in reset_codes:
            return JSONResponse(
                status_code=400,
                content={"detail": "Session de réinitialisation invalide ou expirée"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        reset_data = reset_codes[email]
        
        # Vérifier que le code a été vérifié
        if not reset_data.get("verified", False):
            return JSONResponse(
                status_code=400,
                content={"detail": "Code non vérifié"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier l'expiration
        if datetime.utcnow() > reset_data["expires_at"]:
            del reset_codes[email]
            return JSONResponse(
                status_code=400,
                content={"detail": "Session expirée"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Récupérer l'utilisateur
        user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
        if not user:
            return JSONResponse(
                status_code=404,
                content={"detail": "Utilisateur non trouvé"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Valider la force du mot de passe
        errors = []
        if not any(c.isupper() for c in new_password):
            errors.append("une majuscule")
        if not any(c.islower() for c in new_password):
            errors.append("une minuscule")
        if not any(c.isdigit() for c in new_password):
            errors.append("un chiffre")
        if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in new_password):
            errors.append("un caractère spécial")
        
        if errors:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Le mot de passe doit contenir au moins {', '.join(errors)}"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # ✅ Mettre à jour le mot de passe (déjà tronqué)
        print(f"🔐 Hachage du mot de passe (longueur finale: {len(new_password)})")
        user.passwordHash = get_password_hash(new_password)
        
        # Enregistrer dans l'historique
        login_history = LoginHistory(
            user_id=user.id,
            action="Réinitialisation de mot de passe",
            ip_address="127.0.0.1",
            details="Mot de passe réinitialisé via forgot password"
        )
        db.add(login_history)
        
        # Nettoyer le code
        del reset_codes[email]
        
        db.commit()
        
        print(f"✅ Mot de passe réinitialisé avec succès pour {email}")
        
        return JSONResponse(
            content={"message": "Mot de passe réinitialisé avec succès"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except Exception as e:
        print(f"❌ Erreur dans reset_password: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Erreur serveur: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )


@router.post("/forgot-password/resend")
async def resend_reset_code(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Renvoyer le code OTP
    """
    try:
        # Récupérer les données du body
        data = await request.json()
        email = data.get("email")
        
        print(f"📧 Renvoi de code pour {email}")
        
        if not email:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email requis"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Vérifier si l'email existe
        user = db.query(DashboardUser).filter(DashboardUser.email == email).first()
        
        if not user:
            return JSONResponse(
                content={"message": "Si l'email existe, un nouveau code a été envoyé"},
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:5173",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        
        # Générer un nouveau code OTP
        otp_code = generate_otp()
        print(f"🔐 Nouveau code pour {email}: {otp_code}")
        
        # Stocker le code
        reset_codes[email] = {
            "code": otp_code,
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "attempts": 0,
            "user_id": user.id,
            "verified": False
        }
        
        # Envoyer l'email
        background_tasks.add_task(
            send_reset_password_email,
            email=email,
            full_name=user.fullName,
            otp_code=otp_code
        )
        
        return JSONResponse(
            content={"message": "Nouveau code envoyé"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except Exception as e:
        print(f"❌ Erreur dans resend_reset_code: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Erreur serveur: {str(e)}"},
            headers={
                "Access-Control-Allow-Origin": "http://localhost:5173",
                "Access-Control-Allow-Credentials": "true",
            }
        )