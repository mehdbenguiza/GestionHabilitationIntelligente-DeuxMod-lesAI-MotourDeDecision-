# app/services/mfa_service.py
"""
Service MFA Simulé — Authentification Multi-Facteur pour tickets CRITIQUES (V3.0)
==================================================================================
Génère un code OTP à 6 chiffres avec TTL de 5 minutes.
Stocké en mémoire (dict) — en production bancaire réelle : Redis + TOTP.

Workflow :
  1. Admin clique "Approuver" sur un ticket CRITIQUE
  2. Frontend appelle POST /tickets/{id}/request-mfa
  3. Backend génère un code + le logue (simulé → console/email)
  4. Admin saisit le code dans le modal
  5. Frontend appelle POST /tickets/{id}/approve avec {"mfa_code": "123456"}
  6. Backend vérifie le code avant d'approuver
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Stockage en mémoire : { (ticket_id, username) → {code, expires_at} }
# ─────────────────────────────────────────────────────────────────────────────

_MFA_STORE: dict = {}

MFA_TTL_MINUTES = 5


class MFAService:

    def generate_code(self, ticket_id: int, username: str) -> str:
        """
        Génère un code MFA à 6 chiffres pour (ticket_id, username).
        Le code expire dans MFA_TTL_MINUTES minutes.
        Retourne le code en clair (pour simulation dans la console / email).
        """
        code = "".join(secrets.choice(string.digits) for _ in range(6))
        key  = (ticket_id, username)
        _MFA_STORE[key] = {
            "code":       code,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=MFA_TTL_MINUTES),
            "used":       False,
        }

        # Simulation d'envoi (en production : SMTP / SMS)
        print(f"\n{'='*60}")
        print(f"   MFA CODE [SIMULATION]  Ticket #{ticket_id}")
        print(f"  Utilisateur  : {username}")
        print(f"  Code OTP     : {code}")
        print(f"  Expire dans  : {MFA_TTL_MINUTES} minutes")
        print(f"{'='*60}\n")

        return code

    def verify_code(self, ticket_id: int, username: str, code: str) -> dict:
        """
        Vérifie le code MFA.
        Retourne {valid: bool, reason: str}.
        """
        key = (ticket_id, username)
        entry = _MFA_STORE.get(key)

        if not entry:
            return {"valid": False, "reason": "Code MFA non trouvé ou non généré pour ce ticket."}

        if entry["used"]:
            return {"valid": False, "reason": "Code MFA déjà utilisé."}

        if datetime.now(timezone.utc) > entry["expires_at"]:
            _MFA_STORE.pop(key, None)
            return {"valid": False, "reason": f"Code MFA expiré (TTL: {MFA_TTL_MINUTES} min)."}

        if entry["code"] != code.strip():
            return {"valid": False, "reason": "Code MFA incorrect."}

        # Invalider le code (usage unique)
        entry["used"] = True

        return {"valid": True, "reason": "Code MFA validé avec succès."}

    def is_mfa_required(self, ai_level: Optional[str], score: Optional[int] = None) -> bool:
        """
        Détermine si le MFA est requis pour un ticket donné.
        Requis si : niveau CRITICAL OU score_metier >= 85.
        """
        if ai_level == "CRITICAL":
            return True
        if score is not None and score >= 85:
            return True
        return False

    def cleanup_expired(self):
        """Nettoie les codes expirés du store mémoire."""
        now = datetime.now(timezone.utc)
        expired_keys = [k for k, v in _MFA_STORE.items() if v["expires_at"] < now]
        for k in expired_keys:
            _MFA_STORE.pop(k, None)


# Singleton
mfa_service = MFAService()