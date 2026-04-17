# app/services/profile_service.py
"""
Service de gestion du cycle de vie des profils d'accès.
Responsable de :
  - Génération sécurisée du nom de compte et du mot de passe temporaire
  - Création du profil après approbation du ticket
  - Résolution du système cible selon l'application demandée
  - Révocation des profils
  - Envoi de la notification via email_service (simulation iTop)
"""

import secrets
import string
import unicodedata
import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.access_profile import AccessProfile, ProfileStatus
from app.models.systeme import Systeme
from app.models.ticket import Ticket
from app.services import email_service as mail


# ─────────────────────────────────────────────────────────────────────────────
# Mapping application → code système
# ─────────────────────────────────────────────────────────────────────────────

APP_TO_SYSTEM: dict[str, str] = {
    # Core Banking
    "T24":       "CORE_BANKING",
    "MUREX":     "CORE_BANKING",
    "SWIFT":     "CORE_BANKING",
    # Sécurité & Conformité IT
    "AML_TIDE":  "SECURITE_IT",
    "E_BANKING": "SECURITE_IT",
    # Infrastructure & Métier
    "CRM_SIEBEL": "INFRASTRUCTURE",
    "QUANTARA":   "INFRASTRUCTURE",
}
DEFAULT_SYSTEM_CODE = "INFRASTRUCTURE"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers sécurité
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Convertit les caractères accentués et enlève les caractères non-ASCII."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def generate_account_name(full_name: str, email: str, db: Session) -> str:
    """
    Génère un nom de compte unique au format prénom[0].nom (ex: m.benguiza).
    Si collision en DB → ajoute un suffixe numérique (m.benguiza2, …).
    Fallback : utilise la partie locale de l'email.
    """
    parts = _normalize(full_name.strip()).split()

    if len(parts) >= 2:
        # prénom[0] + "." + nom(s de famille)
        first_initial = parts[0][0]
        last_name     = "".join(parts[1:])
        # Garder uniquement lettres et chiffres
        last_name_clean = "".join(c for c in last_name if c.isalnum())
        base = f"{first_initial}.{last_name_clean}"
    elif email:
        # fallback : partie locale de l'email sans domaine
        base = _normalize(email.split("@")[0]).replace(".", "")[:20]
    else:
        base = "user"

    # Garantir l'unicité
    candidate = base
    counter   = 2
    while db.query(AccessProfile).filter(AccessProfile.account_name == candidate).first():
        candidate = f"{base}{counter}"
        counter  += 1

    return candidate


def generate_temp_password(length: int = 16) -> str:
    """
    Génère un mot de passe temporaire fort :
    - Au moins 1 majuscule, 1 chiffre, 1 symbole
    - Utilise secrets (cryptographiquement sûr)
    """
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits    = string.digits
    symbols   = "!@#$%&*+-="

    # Garantir au moins 1 de chaque catégorie
    mandatory = [
        secrets.choice(uppercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]
    # Compléter avec des chars mixtes
    alphabet  = uppercase + lowercase + digits + symbols
    rest      = [secrets.choice(alphabet) for _ in range(length - len(mandatory))]
    password_chars = mandatory + rest
    # Mélanger pour éviter un pattern prévisible
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def _hash_password(plain: str) -> str:
    """
    Hash du mot de passe via SHA-256 + salt statique de l'app.
    (Pour un vrai système bancaire en prod → utiliser bcrypt ou Argon2)
    """
    salt  = "BIAT_DSI_PFE_SALT_2026"
    token = f"{salt}:{plain}"
    return hashlib.sha256(token.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Service Principal
# ─────────────────────────────────────────────────────────────────────────────

class ProfileService:

    # ── Résolution du système cible ──────────────────────────────────────────

    def resolve_system(self, db: Session, application: str) -> Optional[Systeme]:
        """Retourne le Systeme correspondant à l'application demandée."""
        system_code = APP_TO_SYSTEM.get(application.upper(), DEFAULT_SYSTEM_CODE)
        return db.query(Systeme).filter(Systeme.code == system_code, Systeme.actif == True).first()

    # ── Création du profil après approbation ─────────────────────────────────

    def create_profile_from_ticket(
        self,
        db: Session,
        ticket: Ticket,
        approved_by: str,
    ) -> AccessProfile:
        """
        Crée un profil d'accès complet à partir d'un ticket approuvé.
        Envoie l'email de notification (simulation iTop).
        Efface le mot de passe en clair après envoi.
        """
        # 1. Extraire les détails du ticket
        details      = ticket.requested_access_details or {}
        if isinstance(details, list):
            details  = details[0] if details else {}

        application  = details.get("application", "E_BANKING").upper()
        access_types = details.get("access_types", ["READ"])
        resource     = details.get("resource", "OTHER")
        environments = ticket.requested_environments or ["DEV2"]

        # 2. Résoudre le système cible
        systeme = self.resolve_system(db, application)
        system_id   = systeme.id   if systeme else None
        system_name = systeme.nom  if systeme else "Système cible"

        # 3. Générer les credentials
        account_name  = generate_account_name(
            ticket.employee_name or "Utilisateur",
            ticket.employee_email or "",
            db,
        )
        temp_password = generate_temp_password()
        password_hash = _hash_password(temp_password)

        # 4. Créer l'enregistrement en DB (avec temp_password en clair)
        profile = AccessProfile(
            ticket_id     = ticket.id,
            employee_id   = ticket.employee_id,
            system_id     = system_id,
            account_name  = account_name,
            password_hash = password_hash,
            temp_password = temp_password,          # ← sera effacé après email
            application   = application,
            environments  = environments,
            access_types  = access_types,
            resource      = resource,
            status        = ProfileStatus.ACTIVE,
            created_by    = approved_by,
        )
        db.add(profile)
        db.flush()  # obtenir l'ID sans commit

        # 5. Envoyer l'email de notification (simulation iTop)
        subject, html_body = mail.build_approval_email(
            employee_name = ticket.employee_name or "Utilisateur",
            employee_email= ticket.employee_email or "inconnu@biat.com.tn",
            ticket_ref    = ticket.ref,
            system_name   = system_name,
            application   = application,
            environments  = environments,
            access_types  = access_types,
            account_name  = account_name,
            temp_password = temp_password,
            approved_by   = approved_by,
        )
        email_sent = mail.send_email(
            to_address = ticket.employee_email or settings_fallback_email(),
            subject    = subject,
            html_body  = html_body,
        )

        # 6. Sécurité : effacer le mot de passe en clair après l'envoi
        profile.temp_password         = None
        profile.temp_password_cleared = True
        profile.notification_sent     = email_sent
        profile.notification_sent_at  = datetime.now(timezone.utc) if email_sent else None

        print(
            f"✅ [PROFILE] Profil '{account_name}' créé pour {ticket.employee_name} "
            f"({ticket.ref}) | Email{'✓' if email_sent else '✗'}"
        )
        return profile

    # ── Notification de rejet ────────────────────────────────────────────────

    def notify_rejection(
        self,
        db: Session,
        ticket: Ticket,
        reason: str,
        rejected_by: str,
    ) -> bool:
        """Envoie l'email de rejet (simulation iTop). Retourne True si envoi réussi."""
        details      = ticket.requested_access_details or {}
        if isinstance(details, list):
            details  = details[0] if details else {}

        application  = details.get("application", "Application")
        access_types = details.get("access_types", [])
        environments = ticket.requested_environments or []

        subject, html_body = mail.build_rejection_email(
            employee_name = ticket.employee_name or "Utilisateur",
            employee_email= ticket.employee_email or "inconnu@biat.com.tn",
            ticket_ref    = ticket.ref,
            application   = application,
            environments  = environments,
            access_types  = access_types,
            reason        = reason,
            rejected_by   = rejected_by,
        )
        return mail.send_email(
            to_address = ticket.employee_email or settings_fallback_email(),
            subject    = subject,
            html_body  = html_body,
        )

    # ── Révocation ───────────────────────────────────────────────────────────

    def revoke_profile(
        self,
        db: Session,
        profile_id: int,
        revoked_by: str,
        reason: str = "Révocation manuelle par un administrateur",
    ) -> AccessProfile:
        """Révoque un profil d'accès actif."""
        profile = db.query(AccessProfile).filter(AccessProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"Profil ID={profile_id} introuvable")
        if profile.status == ProfileStatus.REVOKED:
            raise ValueError(f"Profil ID={profile_id} est déjà révoqué")

        profile.status        = ProfileStatus.REVOKED
        profile.revoked_by    = revoked_by
        profile.revoked_reason= reason
        profile.revoked_at    = datetime.now(timezone.utc)
        db.flush()

        print(f"🔒 [PROFILE] Profil '{profile.account_name}' révoqué par {revoked_by}")
        return profile
        
    def reactivate_profile(
        self,
        db: Session,
        profile_id: int,
        reactivated_by: str,
    ) -> AccessProfile:
        """Réactive un profil d'accès révoqué."""
        profile = db.query(AccessProfile).filter(AccessProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"Profil ID={profile_id} introuvable")
        if profile.status == ProfileStatus.ACTIVE:
            raise ValueError(f"Profil ID={profile_id} est déjà actif")

        profile.status = ProfileStatus.ACTIVE
        profile.revoked_by = None
        profile.revoked_reason = None
        profile.revoked_at = None
        db.flush()

        print(f"🔓 [PROFILE] Profil '{profile.account_name}' réactivé par {reactivated_by}")
        return profile

    # ── Listing ──────────────────────────────────────────────────────────────

    def get_profiles(self, db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 100):
        query = db.query(AccessProfile)
        if status:
            query = query.filter(AccessProfile.status == status)
        return query.order_by(AccessProfile.created_at.desc()).offset(skip).limit(limit).all()

    def get_profile_by_id(self, db: Session, profile_id: int) -> Optional[AccessProfile]:
        return db.query(AccessProfile).filter(AccessProfile.id == profile_id).first()


def settings_fallback_email() -> str:
    """Retourne l'email de test configuré dans .env (fallback si l'employé n'a pas d'email)."""
    from app.core.config import settings
    return settings.SMTP_USERNAME


# Singleton
profile_service = ProfileService()
