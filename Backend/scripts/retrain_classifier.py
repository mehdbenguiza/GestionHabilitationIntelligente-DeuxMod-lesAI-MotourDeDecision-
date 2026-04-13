# scripts/retrain_classifier.py
"""
Boucle de rétroaction (Active Learning / Feedback Loop)
=======================================================
Ce script :
  1. Charge le dataset d'entraînement historique (CSV).
  2. Récupère depuis la base de données tous les tickets qui ont été
     traités manuellement par un admin/super-admin (approuvés ou rejetés).
     → Ces tickets comportent un signal "humain" fiable.
  3. Construit un DataFrame de nouveaux exemples labellisés.
  4. Fusionne les deux datasets et ré-entraîne le modèle.
  5. Sauvegarde les nouveaux .pkl (feature_extractor + classifier).
  6. Écrit un fichier metrics_history.json pour tracer l'évolution.

Usage :
    cd d:\\ProjetPFE\\Backend
    python scripts/retrain_classifier.py
"""

import os
import sys
import json
import pandas as pd
import joblib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

from app.database import SessionLocal
from app.models.ticket import Ticket, TicketStatus
from app.models.classification_result import ClassificationResult
from app.models.decision_engine import DecisionEngine
from app.services.feature_extractor import FeatureExtractor

# ==================== CONFIG ====================

DATA_DIR   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
CSV_PATH   = os.path.join(DATA_DIR, "training_dataset.csv")
HIST_PATH  = os.path.join(MODEL_DIR, "metrics_history.json")

VALID_LABELS = {"BASE", "SENSITIVE", "CRITICAL"}

# Suppression du mapping statique, remplacé par une logique dynamique plus bas

# ==================== 1. CHARGEMENT DATASET HISTORIQUE ====================

print("=" * 60)
print("[RETRAIN] RÉTRO-ENTRAÎNEMENT DU MODÈLE (Feedback Loop)")
print("=" * 60)

if not os.path.exists(CSV_PATH):
    print(f"[!] Dataset introuvable : {CSV_PATH}")
    print("    Lancez d'abord : python scripts/generate_training_data.py")
    sys.exit(1)

df_hist = pd.read_csv(CSV_PATH)
print(f"\n[FILE] Dataset historique : {len(df_hist)} tickets")

# ==================== 2. TICKETS HUMAINS DEPUIS LA DB ====================

print("\n[DB] Connexion à la base de données...")
db = SessionLocal()
try:
    # Tickets traités manuellement (approuvés ou rejetés)
    human_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_([TicketStatus.APPROVED, TicketStatus.REJECTED]))
        .all()
    )
    print(f"[OK] {len(human_tickets)} tickets humains récupérés")

    new_rows = []
    for t in human_tickets:
        details = t.requested_access_details or {}
        envs    = t.requested_environments or []

        if t.status == TicketStatus.APPROVED:
            if details.get("environment") == "PRD" or (envs and envs[0] == "PRD"):
                label = "SENSITIVE"
            else:
                label = "BASE"
        elif t.status == TicketStatus.REJECTED:
            label = "CRITICAL"
        else:
            continue

        row = {
            "team":                    t.team_name or "MOE",
            "role":                    t.role or "DEVELOPPEUR",
            "application":             details.get("application", "E_BANKING"),
            "environment":             envs[0] if envs else "DEV2",
            "access_type":             (details.get("access_types") or ["READ"])[0],
            "resource":                details.get("resource", "OTHER"),
            "user_seniority":          details.get("user_seniority", "senior"),
            "request_reason":          details.get("request_reason", "maintenance_preventive"),
            "manager_approval_status": details.get("manager_approval_status", "none"),
            "label":                   label,
        }
        new_rows.append(row)

    if new_rows:
        df_human = pd.DataFrame(new_rows)
        print(f"\n[STATS] Distribution labels humains :")
        print(df_human["label"].value_counts())
    else:
        df_human = pd.DataFrame()
        print("[INFO] Aucun ticket humain utilisable (tous en statut NEW/ASSIGNED ?)")

    # ─── Corrections humaines (chaque correction = 5 exemples) ───────────
    print("\n[LIB] Chargement des corrections humaines de la bibliothèque...")
    try:
        from app.models.ai_feedback import AICorrection
        corrections = db.query(AICorrection).all()
        correction_rows = []
        for c in corrections:
            base_row = {
                "team":                    c.team,
                "role":                    "DEVELOPPEUR",        # rôle générique
                "application":             c.application,
                "environment":             c.environment,
                "access_type":             c.access_type,
                "resource":                c.resource or "OTHER",
                "user_seniority":          "junior",
                "request_reason":          "maintenance_preventive",
                "manager_approval_status": "none",
                "label":                   c.corrected_level,
            }
            import random
            weight = random.randint(2, 3)
            for _ in range(weight):
                correction_rows.append(base_row.copy())
        if correction_rows:
            df_human_corrections = pd.DataFrame(correction_rows)
            print(f"[OK] {len(corrections)} corrections -> {len(correction_rows)} exemples d'entraînement")
        else:
            df_human_corrections = pd.DataFrame()
            print("[INFO] Aucune correction dans la bibliothèque.")
    except Exception as ce:
        df_human_corrections = pd.DataFrame()
        print(f"[WARN] Impossible de charger les corrections : {ce}")

finally:
    db.close()

# ==================== 3. FUSION ====================

if not df_human.empty and not df_human_corrections.empty:
    df_combined = pd.concat([df_hist, df_human, df_human_corrections], ignore_index=True)
    print(f"\n[JOIN] Dataset combiné : {len(df_combined)} tickets "
          f"({len(df_hist)} historiques + {len(df_human)} humains + {len(df_human_corrections)} corrections)")
elif not df_human.empty:
    df_combined = pd.concat([df_hist, df_human], ignore_index=True)
    print(f"\n[JOIN] Dataset combiné : {len(df_combined)} tickets "
          f"({len(df_hist)} historiques + {len(df_human)} humains)")
elif not df_human_corrections.empty:
    df_combined = pd.concat([df_hist, df_human_corrections], ignore_index=True)
    print(f"\n[JOIN] Dataset combiné : {len(df_combined)} tickets "
          f"({len(df_hist)} historiques + {len(df_human_corrections)} corrections)")
else:
    df_combined = df_hist
    print("\n[INFO] Ré-entraînement sur le dataset historique uniquement.")


# ==================== 4. PRÉPARATION DES FEATURES ====================

print("\n[WORK] Préparation des features...")
extractor = FeatureExtractor()
extractor.fit(df_combined)
X = extractor.transform(df_combined)
y = df_combined["label"]

print(f"[STATS] Features : {X.shape[1]} colonnes")
print(f"[STATS] Labels   : {y.value_counts().to_dict()}")

# ==================== 5. ENTRAÎNEMENT ====================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n[TRAIN] Entraînement Random Forest sur {len(X_train)} tickets...")
model = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    random_state=42,
    class_weight="balanced",
)
model.fit(X_train, y_train)

# ==================== 6. ÉVALUATION ====================

y_pred  = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
cv_scores = cross_val_score(model, X, y, cv=5)

print(f"\n[SCORE] Accuracy : {accuracy:.2%}")
print(f"[STATS] CV Moyenne : {cv_scores.mean():.2%}  (±{cv_scores.std():.2%})")
print("\n[REPORT] Classification Report :")
print(classification_report(y_test, y_pred))

# ==================== 7. SAUVEGARDE ====================

os.makedirs(MODEL_DIR, exist_ok=True)

extractor_path = os.path.join(MODEL_DIR, "feature_extractor.pkl")
model_path     = os.path.join(MODEL_DIR, "classifier_model.pkl")

extractor.save(extractor_path)
joblib.dump(model, model_path)
print(f"\n[SAVE] Modèle sauvegardé      : {model_path}")
print(f"[SAVE] Extracteur sauvegardé  : {extractor_path}")

# ==================== 8. HISTORIQUE DES MÉTRIQUES ====================

history = []
if os.path.exists(HIST_PATH):
    with open(HIST_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)

history.append({
    "date":             datetime.utcnow().isoformat(),
    "total_tickets":    len(df_combined),
    "human_tickets":    len(df_human),
    "accuracy":         round(accuracy, 4),
    "cv_mean":          round(float(cv_scores.mean()), 4),
    "cv_std":           round(float(cv_scores.std()), 4),
    "label_distribution": y.value_counts().to_dict(),
})

with open(HIST_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"\n[DONE] Historique métriques mis à jour : {HIST_PATH}")
print("\n[OK] Rétro-entraînement terminé avec succès !")
print(f"    -> Le modèle est désormais plus intelligent grâce aux feedbacks humains.")
