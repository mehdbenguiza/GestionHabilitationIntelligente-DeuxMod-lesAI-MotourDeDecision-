"""
migrate_anomaly_v1.py
=====================
Migration pour le Modèle 2 — Détection d'Anomalies.

Opérations :
  1. Ajouter colonnes `source` et `employee_submitted_at` à la table `tickets`
  2. Créer la table `anomaly_logs`
  3. Initialiser `source = "ITOP"` pour les tickets existants
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, Base

# Import des modèles pour que SQLAlchemy les connaisse
from app.models.ticket import Ticket
from app.models.anomaly_log import AnomalyLog   # sera créé à l'étape 5


def run_migration():
    print("=" * 60)
    print("  Migration Anomaly V1 — Modèle 2 Détection d'Anomalies")
    print("=" * 60)

    with engine.connect() as conn:

        # ── 1. Ajouter colonne `source` à tickets ───────────────────────────
        try:
            conn.execute(text(
                "ALTER TABLE tickets ADD COLUMN source VARCHAR(30) NOT NULL DEFAULT 'ITOP'"
            ))
            conn.commit()
            print("✅ Colonne `source` ajoutée à tickets")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Colonne `source` déjà présente — ignoré")
            else:
                print(f"⚠️  source: {e}")

        # ── 2. Ajouter colonne `employee_submitted_at` à tickets ────────────
        try:
            conn.execute(text(
                "ALTER TABLE tickets ADD COLUMN employee_submitted_at DATETIME NULL"
            ))
            conn.commit()
            print("✅ Colonne `employee_submitted_at` ajoutée à tickets")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  Colonne `employee_submitted_at` déjà présente — ignoré")
            else:
                print(f"⚠️  employee_submitted_at: {e}")

        # ── 3. Initialiser source="ITOP" pour les tickets existants ─────────
        try:
            result = conn.execute(text(
                "UPDATE tickets SET source = 'ITOP' WHERE source IS NULL OR source = ''"
            ))
            conn.commit()
            print(f"✅ {result.rowcount} tickets existants initialisés avec source='ITOP'")
        except Exception as e:
            print(f"⚠️  Init source: {e}")

    # ── 4. Créer la table anomaly_logs via SQLAlchemy ───────────────────────
    try:
        AnomalyLog.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table `anomaly_logs` créée (ou déjà existante)")
    except Exception as e:
        print(f"⚠️  anomaly_logs: {e}")

    print("\n✅ Migration Anomaly V1 terminée avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
