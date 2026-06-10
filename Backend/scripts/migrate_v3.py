# scripts/migrate_v3.py
"""
Script de Migration DB — V3.0
==============================
Ajoute les nouvelles colonnes nécessaires pour la V3.0 sans perdre de données.
Toutes les opérations sont des ADD COLUMN avec valeurs par défaut.

100% SAFE : ne supprime ni ne modifie de données existantes.

Usage :
    cd d:\\ProjetPFE\\Backend
    venv\\Scripts\\python scripts\\migrate_v3.py
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.database import engine

SEPARATOR = "=" * 60


def column_exists(table: str, column: str) -> bool:
    """Vérifie si une colonne existe via SQLAlchemy Inspector."""
    inspector = inspect(engine)
    columns = inspector.get_columns(table)
    return any(c["name"] == column for c in columns)


def add_column_safe(conn, table: str, column: str, col_type: str, default=None):
    """Ajoute une colonne si elle n'existe pas déjà."""
    if column_exists(table, column):
        print(f"   ⏭️  {table}.{column} — déjà présente, ignorée")
        return

    default_clause = f" DEFAULT {default}" if default is not None else ""
    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
    conn.execute(text(sql))
    print(f"   ✅ {table}.{column} ({col_type}) — ajoutée")


def run_migration():
    print(f"\n{SEPARATOR}")
    print("  MIGRATION V3.0 — Gestion Habilitations BIAT")
    print(f"{SEPARATOR}")

    with engine.connect() as conn:

        # ────────────────────────────────────────────────────────────────────
        # TABLE employees — Trust Score (Phase 4)
        # ────────────────────────────────────────────────────────────────────
        print("\n📋 TABLE: employees (Trust Score)")
        add_column_safe(conn, "employees", "trust_score",       "REAL",    default=100.0)
        add_column_safe(conn, "employees", "total_requests",    "INTEGER", default=0)
        add_column_safe(conn, "employees", "approved_requests", "INTEGER", default=0)
        add_column_safe(conn, "employees", "rejected_requests", "INTEGER", default=0)

        # ────────────────────────────────────────────────────────────────────
        # TABLE classification_results — SHAP + NLP (Phases 2 & 3)
        # ────────────────────────────────────────────────────────────────────
        print("\n📋 TABLE: classification_results (SHAP + NLP)")
        add_column_safe(conn, "classification_results", "shap_values",    "JSON",    default=None)
        add_column_safe(conn, "classification_results", "nlp_score",      "INTEGER", default=None)
        add_column_safe(conn, "classification_results", "nlp_label",      "VARCHAR(30)", default=None)
        add_column_safe(conn, "classification_results", "trust_modifier", "INTEGER", default=None)

        # ────────────────────────────────────────────────────────────────────
        # TABLE access_profiles — JIT Access (Phase 6)
        # ────────────────────────────────────────────────────────────────────
        print("\n📋 TABLE: access_profiles (JIT Access)")
        add_column_safe(conn, "access_profiles", "expiry_hours", "INTEGER", default=None)
        add_column_safe(conn, "access_profiles", "auto_revoked", "BOOLEAN", default=0)

        conn.commit()

    print(f"\n{SEPARATOR}")
    print("  ✅ Migration V3.0 terminée avec succès !")
    print("  → Toutes les nouvelles colonnes sont disponibles.")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    run_migration()
