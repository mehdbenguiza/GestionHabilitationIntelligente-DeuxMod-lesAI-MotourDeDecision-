"""
train_anomaly_model.py
======================
Entraîne le Modèle 2 : Détection d'Anomalies Comportementales
basé sur l'algorithme Isolation Forest (scikit-learn).

Features comportementales :
  - submission_hour       : heure de soumission (0-23)
  - submission_weekday    : jour de la semaine (0=Lundi … 6=Dimanche)
  - is_weekend            : 1 si Sa/Di, 0 sinon
  - is_out_of_hours       : 1 si hors 07h-18h, 0 sinon
  - tickets_today         : nombre de tickets soumis ce jour par cet employé
  - tickets_week          : nombre de tickets cette semaine

Seuils métier :
  - Horaires normaux : 07h00 – 18h00 (08h00 – 17h00 ± 1h marge)
  - Jours ouvrés : Lundi (0) – Vendredi (4)
  - Volume normal : 1-3 tickets/jour
  - Volume suspect : 4-5 tickets/jour (LOW)
  - Volume anormal : 6-7 tickets/jour (MEDIUM)
  - Volume critique : 8+ tickets/jour (HIGH)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ─────────────────────────────────────────────────────────────────────────────
# 1. Génération du dataset synthétique
# ─────────────────────────────────────────────────────────────────────────────

np.random.seed(42)

NORMAL_SIZE   = 2000   # 80% : comportement normal
ANOMALY_SIZE  = 500    # 20% : comportements anormaux

# ── Comportement NORMAL ────────────────────────────────────────────────────
# Lundi-Vendredi (0-4), entre 7h et 18h, 1-3 tickets/jour
normal_hours    = np.random.randint(7, 18, NORMAL_SIZE)
normal_weekday  = np.random.randint(0, 5, NORMAL_SIZE)   # 0=Lundi…4=Vendredi
normal_weekend  = np.zeros(NORMAL_SIZE)
normal_oor      = np.zeros(NORMAL_SIZE)
normal_today    = np.random.randint(1, 4, NORMAL_SIZE)   # 1 à 3 tickets/jour
normal_week     = np.random.randint(1, 8, NORMAL_SIZE)   # 1 à 7 tickets/semaine

normal_data = np.column_stack([
    normal_hours,
    normal_weekday,
    normal_weekend,
    normal_oor,
    normal_today,
    normal_week,
])

# ── Comportements ANORMAUX (plusieurs patterns) ────────────────────────────
anom_per_type = ANOMALY_SIZE // 4

# Type 1 : Soumission la nuit (23h-6h)
a1_hours   = np.random.choice(list(range(0, 7)) + list(range(18, 24)), anom_per_type)
a1_weekday = np.random.randint(0, 5, anom_per_type)
a1_weekend = np.zeros(anom_per_type)
a1_oor     = np.ones(anom_per_type)
a1_today   = np.random.randint(1, 4, anom_per_type)
a1_week    = np.random.randint(1, 8, anom_per_type)

# Type 2 : Soumission le weekend
a2_hours   = np.random.randint(7, 18, anom_per_type)
a2_weekday = np.random.choice([5, 6], anom_per_type)   # Sa=5, Di=6
a2_weekend = np.ones(anom_per_type)
a2_oor     = np.zeros(anom_per_type)
a2_today   = np.random.randint(1, 4, anom_per_type)
a2_week    = np.random.randint(1, 8, anom_per_type)

# Type 3 : Volume excessif (6+ tickets/jour)
a3_hours   = np.random.randint(7, 18, anom_per_type)
a3_weekday = np.random.randint(0, 5, anom_per_type)
a3_weekend = np.zeros(anom_per_type)
a3_oor     = np.zeros(anom_per_type)
a3_today   = np.random.randint(6, 15, anom_per_type)   # 6-14 tickets/jour
a3_week    = np.random.randint(10, 30, anom_per_type)

# Type 4 : Combiné (weekend + nuit + volume)
a4_hours   = np.random.choice(list(range(0, 7)) + list(range(18, 24)), anom_per_type)
a4_weekday = np.random.choice([5, 6], anom_per_type)
a4_weekend = np.ones(anom_per_type)
a4_oor     = np.ones(anom_per_type)
a4_today   = np.random.randint(4, 12, anom_per_type)
a4_week    = np.random.randint(8, 25, anom_per_type)

anomaly_data = np.vstack([
    np.column_stack([a1_hours, a1_weekday, a1_weekend, a1_oor, a1_today, a1_week]),
    np.column_stack([a2_hours, a2_weekday, a2_weekend, a2_oor, a2_today, a2_week]),
    np.column_stack([a3_hours, a3_weekday, a3_weekend, a3_oor, a3_today, a3_week]),
    np.column_stack([a4_hours, a4_weekday, a4_weekend, a4_oor, a4_today, a4_week]),
])

# Dataset complet (pour le scaler, on entraîne uniquement sur les normaux)
X_train = normal_data   # Isolation Forest s'entraîne sur les données normales
X_all   = np.vstack([normal_data, anomaly_data])
y_all   = np.array([1] * NORMAL_SIZE + [-1] * ANOMALY_SIZE)  # 1=normal, -1=anomalie

print(f"Dataset : {NORMAL_SIZE} normaux + {ANOMALY_SIZE} anomalies = {len(X_all)} total")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Normalisation des features
# ─────────────────────────────────────────────────────────────────────────────

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_all_scaled   = scaler.transform(X_all)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Entraînement Isolation Forest
# ─────────────────────────────────────────────────────────────────────────────

model = IsolationForest(
    n_estimators=300,
    max_samples="auto",
    contamination=0.2,     # 20% d'anomalies dans le dataset synthétique
    random_state=42,
    n_jobs=-1,
)
model.fit(X_all_scaled)    # On apprend à distinguer les deux distributions

print("INFO: Isolation Forest entraine")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Évaluation
# ─────────────────────────────────────────────────────────────────────────────

predictions = model.predict(X_all_scaled)
# Isolation Forest : 1=normal, -1=anomalie
true_anomalies     = (y_all == -1).sum()
detected_anomalies = (predictions == -1).sum()
correct_detections = ((predictions == -1) & (y_all == -1)).sum()
false_positives    = ((predictions == -1) & (y_all == 1)).sum()

precision = correct_detections / detected_anomalies if detected_anomalies > 0 else 0
recall    = correct_detections / true_anomalies if true_anomalies > 0 else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print("\nStats Isolation Forest :")
print(f"   Anomalies réelles    : {true_anomalies}")
print(f"   Anomalies détectées  : {detected_anomalies}")
print(f"   Vraies détections    : {correct_detections}")
print(f"   Faux positifs        : {false_positives}")
print(f"   Précision            : {precision:.2%}")
print(f"   Rappel               : {recall:.2%}")
print(f"   Score F1             : {f1:.2%}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Sauvegarde
# ─────────────────────────────────────────────────────────────────────────────

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

model_path  = os.path.join(MODELS_DIR, "anomaly_detector.pkl")
scaler_path = os.path.join(MODELS_DIR, "anomaly_scaler.pkl")

joblib.dump(model,  model_path)
joblib.dump(scaler, scaler_path)

print(f"\nModel sauvegarde  : {model_path}")
print(f"Scaler sauvegarde  : {scaler_path}")
print("\nEntrainement Modele 2 termine avec succes !")

# Noms des features (pour documentation)
FEATURE_NAMES = [
    "submission_hour",
    "submission_weekday",
    "is_weekend",
    "is_out_of_hours",
    "tickets_today",
    "tickets_week",
]
print(f"\nFeatures utilisées : {FEATURE_NAMES}")
