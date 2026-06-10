# app/tasks/auto_retrain_task.py
"""
Tâche Active Learning — Rétro-Entraînement Automatique (V3.0)
=============================================================
Déclenchée automatiquement quand le cumul de "dislikes" corrigés
atteint le seuil RETRAIN_THRESHOLD (défaut: 10 corrections).

Workflow :
  1. L'Admin/SuperAdmin soumet un "dislike" + correction sur un ticket
  2. Le feedback endpoint compte les corrections non-traitées
  3. Si count >= RETRAIN_THRESHOLD → déclenche cette BackgroundTask
  4. La tâche ré-entraîne le modèle XGBoost avec les nouvelles données
  5. Notifie via AuditService que le modèle a été mis à jour
"""

import os
import sys
import subprocess
from datetime import datetime, timezone

# Seuil pour déclencher le rétro-entraînement
RETRAIN_THRESHOLD = 10

# Compteur partagé en mémoire (thread-safe pour usage mono-instance)
_pending_dislike_count: int = 0
_last_retrain_at: datetime | None = None


def increment_dislike_counter() -> int:
    """Incrémente le compteur et retourne la valeur actuelle."""
    global _pending_dislike_count
    _pending_dislike_count += 1
    return _pending_dislike_count


def reset_dislike_counter():
    global _pending_dislike_count
    _pending_dislike_count = 0


def get_counter_status() -> dict:
    return {
        "pending_dislikes":     _pending_dislike_count,
        "retrain_threshold":    RETRAIN_THRESHOLD,
        "last_retrain_at":      _last_retrain_at.isoformat() if _last_retrain_at else None,
        "next_retrain_at":      f"{RETRAIN_THRESHOLD - _pending_dislike_count} corrections restantes",
    }


def should_retrain() -> bool:
    """Retourne True si le seuil est atteint."""
    return _pending_dislike_count >= RETRAIN_THRESHOLD


def run_retrain_background(db=None):
    """
    Exécute le rétro-entraînement en arrière-plan.
    Appelé via FastAPI BackgroundTasks.
    """
    global _last_retrain_at

    print(f"\n{'='*60}")
    print(f"  🤖 [ACTIVE LEARNING] Seuil atteint ({_pending_dislike_count} dislikes)")
    print(f"  Démarrage du rétro-entraînement XGBoost automatique...")
    print(f"{'='*60}")

    try:
        # Trouver le chemin du script
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        script_path = os.path.join(base_dir, "scripts", "retrain_classifier.py")
        venv_python = os.path.join(base_dir, "venv", "Scripts", "python.exe")

        if not os.path.exists(venv_python):
            venv_python = sys.executable  # Fallback: python courant

        # Lancer le script de rétro-entraînement
        result = subprocess.run(
            [venv_python, script_path],
            capture_output=True,
            text=True,
            cwd=base_dir,
            timeout=300,  # Max 5 minutes
        )

        _last_retrain_at = datetime.now(timezone.utc)
        reset_dislike_counter()

        if result.returncode == 0:
            print("✅ [ACTIVE LEARNING] Rétro-entraînement XGBoost terminé avec succès !")
            print(f"   Sortie : {result.stdout[-500:] if result.stdout else 'OK'}")

            # Notifier
            if db:
                try:
                    from app.services.audit_service import audit_service
                    audit_service.notify(
                        db=db,
                        title="🤖 Active Learning : Modèle IA mis à jour",
                        message=(
                            f"Le modèle XGBoost a été ré-entraîné automatiquement "
                            f"suite à {RETRAIN_THRESHOLD} corrections humaines."
                        ),
                        type="info",
                    )
                    db.commit()
                except Exception as e:
                    print(f"⚠️ [ACTIVE LEARNING] Erreur notification: {e}")
        else:
            print(f"❌ [ACTIVE LEARNING] Échec du rétro-entraînement!")
            print(f"   Erreur : {result.stderr[-500:] if result.stderr else 'Inconnue'}")

    except subprocess.TimeoutExpired:
        print("❌ [ACTIVE LEARNING] Timeout dépassé (5 min) pendant le rétro-entraînement")
    except Exception as e:
        print(f"❌ [ACTIVE LEARNING] Erreur inattendue : {e}")
