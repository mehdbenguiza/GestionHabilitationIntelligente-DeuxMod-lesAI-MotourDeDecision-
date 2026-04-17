# scripts/import_employees_excel.py
"""
Import du dataset employés (Excel) vers la table `employees` en base de données.
- Lit le fichier : data/employees_dataset_250.xlsx
- Insère uniquement les nouveaux (skip si id déjà présent)
- Compatible MySQL & SQLite

Usage :
    cd d:\\ProjetPFE\\Backend
    python scripts/import_employees_excel.py
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.employee import Employee

# -- Chemin du fichier Excel ----------------------------------------------------
EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "employees_dataset_250.xlsx"
)

# -- Valeurs valides -------------------------------------------------------------
VALID_TEAMS = {
    "MOE", "MOA", "RESEAU", "SECURITE", "TEST_FACTORY",
    "DATA", "MXP", "CONFORMITE", "MONETIQUE", "TRADING", "AUDIT_INTERNE"
}
VALID_SENIORITY = {"junior", "senior"}


def run():
    print("=" * 60)
    print("[IMPORT] Importation des employés depuis Excel -> DB")
    print("=" * 60)

    # 1. Lecture du fichier
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERREUR] Fichier introuvable : {EXCEL_PATH}")
        sys.exit(1)

    df = pd.read_excel(EXCEL_PATH)
    print(f"[OK] {len(df)} employés lus depuis le fichier Excel")

    # 2. Validation des colonnes
    required = {"id", "name", "email", "team", "role", "seniority"}
    missing = required - set(df.columns)
    if missing:
        print(f"[ERREUR] Colonnes manquantes : {missing}")
        sys.exit(1)

    # 3. Nettoyage
    df["id"]        = df["id"].astype(str).str.strip()
    df["name"]      = df["name"].astype(str).str.strip()
    df["email"]     = df["email"].astype(str).str.strip().str.lower()
    df["team"]      = df["team"].astype(str).str.strip().str.upper()
    df["role"]      = df["role"].astype(str).str.strip().str.upper()
    df["seniority"] = df["seniority"].astype(str).str.strip().str.lower()

    # Créer la table si elle n'existe pas encore
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inserted = 0
    skipped  = 0
    errors   = 0

    try:
        for _, row in df.iterrows():
            emp_id = row["id"]

            # Validation séniorité
            seniority = row["seniority"]
            if seniority not in VALID_SENIORITY:
                seniority = "junior"  # fallback

            # Validation team
            team = row["team"]
            if team not in VALID_TEAMS:
                print(f"  [WARN] Équipe inconnue '{team}' pour {emp_id} — ignorée")
                errors += 1
                continue

            # Vérifier si l'employé existe déjà
            existing = db.query(Employee).filter(Employee.id == emp_id).first()
            if existing:
                skipped += 1
                continue

            employee = Employee(
                id        = emp_id,
                name      = row["name"],
                email     = row["email"],
                team      = team,
                role      = row["role"],
                seniority = seniority,
            )
            db.add(employee)
            inserted += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"[ERREUR] Transaction annulée : {e}")
        sys.exit(1)
    finally:
        db.close()

    # -- Résumé ----------------------------------------------------------------
    print(f"\n[RESUME]")
    print(f"  [OK] Insérés   : {inserted}")
    print(f"  [SKIP] Skippés : {skipped} (déjà présents)")
    print(f"  [ERR] Erreurs  : {errors}")

    total_db = SessionLocal().query(Employee).count()
    print(f"\n[DB] Total employés en base : {total_db}")
    print("\n[DONE] Import terminé avec succès !")


if __name__ == "__main__":
    run()
