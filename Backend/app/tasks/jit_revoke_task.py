# app/tasks/jit_revoke_task.py
"""
Tâche JIT (Just-In-Time) — Révocation Automatique des Accès Expirés (V3.0)
===========================================================================
Tourne en arrière-plan toutes les 15 minutes.
Révoque automatiquement les profils d'accès dont la date d'expiration est passée.

Workflow :
  1. Lancée au démarrage de l'app (main.py startup_event)
  2. Vérifie toutes les 15 min les profils ACTIVE avec expires_at < now()
  3. Les passe en status=EXPIRED + auto_revoked=True
  4. Notifie via AuditService
"""

import asyncio
from datetime import datetime, timezone

JIT_CHECK_INTERVAL_SECONDS = 15 * 60  # 15 minutes


async def jit_revoke_loop():
    """
    Boucle asyncio lancée au démarrage de l'application.
    S'exécute en permanence en arrière-plan.
    """
    print("[JIT] [OK] Tâche de révocation automatique démarrée (intervalle: 15 min)")

    while True:
        try:
            await _revoke_expired_profiles()
        except Exception as e:
            print(f"[JIT] [WARN] Erreur dans la boucle JIT : {e}")

        await asyncio.sleep(JIT_CHECK_INTERVAL_SECONDS)


async def _revoke_expired_profiles():
    """Révoque tous les profils expirés."""
    from app.database import SessionLocal
    from app.models.access_profile import AccessProfile, ProfileStatus
    from app.services.audit_service import audit_service

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Chercher les profils actifs avec une date d'expiration dépassée
        expired = (
            db.query(AccessProfile)
            .filter(
                AccessProfile.status   == ProfileStatus.ACTIVE,
                AccessProfile.expires_at != None,
                AccessProfile.expires_at <= now,
            )
            .all()
        )

        if not expired:
            return

        print(f"[JIT] [TIME] {len(expired)} profil(s) expiré(s) détecté(s) — Révocation en cours...")

        for profile in expired:
            profile.status       = ProfileStatus.EXPIRED
            profile.auto_revoked = True
            profile.revoked_at   = now
            profile.revoked_by   = "Système JIT Automatique"
            profile.revoked_reason = (
                f"Accès temporaire expiré automatiquement "
                f"(durée configurée : {profile.expiry_hours}h)"
            )

            print(f"   [LOCK] Profil '{profile.account_name}' (ID={profile.id}) → EXPIRED")

            # Notifier
            try:
                audit_service.notify(
                    db=db,
                    title=f"[TIME] Accès Temporaire Expiré : {profile.account_name}",
                    message=(
                        f"Le compte '{profile.account_name}' a été révoqué automatiquement "
                        f"après {profile.expiry_hours}h (politique JIT)."
                    ),
                    type="warning",
                )
            except Exception:
                pass

        db.commit()
        print(f"[JIT] [OK] {len(expired)} profil(s) révoqué(s) avec succès")

    except Exception as e:
        db.rollback()
        print(f"[JIT] [FAIL] Erreur révocation : {e}")
    finally:
        db.close()
