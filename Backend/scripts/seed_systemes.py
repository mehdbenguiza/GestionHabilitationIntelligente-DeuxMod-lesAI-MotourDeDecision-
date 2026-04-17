# scripts/seed_systemes.py
"""
Script de seed pour créer les 3 systèmes d'information de référence BIAT.
Appelé automatiquement au démarrage de l'application si la table est vide.
Peut aussi être exécuté manuellement : python -m scripts.seed_systemes
"""

from sqlalchemy.orm import Session


# ─────────────────────────────────────────────────────────────────────────────
# Données de référence — Les 3 Systèmes SI de la banque
# ─────────────────────────────────────────────────────────────────────────────

SYSTEMES_DATA = [
    {
        "code":        "CORE_BANKING",
        "nom":         "Core Banking",
        "description": (
            "Système central de traitement bancaire. "
            "Regroupe les applications critiques de front-office et back-office : "
            "T24 (Temenos), MUREX (trading & marchés financiers) et SWIFT (messagerie interbancaire). "
            "Accès strictement contrôlé — Niveau de sensibilité CRITIQUE."
        ),
        "applications":       ["T24", "MUREX", "SWIFT"],
        "environments":       ["DEV2", "DVR", "TST", "QL2", "CRT", "UAT", "INV", "PRD"],
        "sensibilite":        "CRITICAL",
        "responsable_email":  "dsi-corebanking@biat.com.tn",
        "actif":              True,
    },
    {
        "code":        "SECURITE_IT",
        "nom":         "Sécurité & Conformité IT",
        "description": (
            "Périmètre des outils de conformité réglementaire et de sécurité bancaire. "
            "Inclut AML_TIDE (lutte anti-blanchiment) et la plateforme E-Banking. "
            "Soumis aux exigences BCT (Banque Centrale de Tunisie) et directives FATCA/AML. "
            "Niveau de sensibilité SENSIBLE."
        ),
        "applications":       ["AML_TIDE", "E_BANKING"],
        "environments":       ["DEV2", "TST", "QL2", "UAT", "PRD"],
        "sensibilite":        "SENSITIVE",
        "responsable_email":  "dsi-securite@biat.com.tn",
        "actif":              True,
    },
    {
        "code":        "INFRASTRUCTURE",
        "nom":         "Infrastructure & Outils Métier",
        "description": (
            "Systèmes d'outillage transversal : CRM Siebel (gestion relation client) "
            "et QUANTARA (analyse quantitative et reporting). "
            "Environnements de développement et tests principalement. "
            "Niveau de sensibilité BASE."
        ),
        "applications":       ["CRM_SIEBEL", "QUANTARA"],
        "environments":       ["DEV2", "DVR", "TST", "QL2"],
        "sensibilite":        "BASE",
        "responsable_email":  "dsi-infra@biat.com.tn",
        "actif":              True,
    },
]


def seed_systemes(db: Session) -> None:
    """Insère les systèmes de référence dans la base si absents."""
    from app.models.systeme import Systeme

    created = 0
    for data in SYSTEMES_DATA:
        existing = db.query(Systeme).filter(Systeme.code == data["code"]).first()
        if not existing:
            systeme = Systeme(**data)
            db.add(systeme)
            created += 1
            print(f"  ✅ [SEED] Système créé : {data['nom']} ({data['code']})")

    if created > 0:
        db.commit()
        print(f"  📦 [SEED] {created} système(s) ajouté(s) en base.")
    else:
        print("  ℹ️  [SEED] Tous les systèmes existent déjà.")


# ─── Exécution manuelle ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import os

    # Résoudre le chemin du projet
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.database import SessionLocal, engine, Base

    # Créer les tables si nécessaire
    import app.models.systeme      # noqa — force SQLAlchemy à les connaître
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_systemes(db)
    finally:
        db.close()

    print("✅ Seed terminé.")
