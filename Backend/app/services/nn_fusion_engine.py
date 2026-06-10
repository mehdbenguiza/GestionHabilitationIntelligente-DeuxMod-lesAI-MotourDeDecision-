# app/services/nn_fusion_engine.py
"""
Moteur de Décision par Réseau de Neurones (MLP) — Fusion Tri-Polaire
=====================================================================
Remplace le moteur de fusion à table statique par un MLP (Multi-Layer
Perceptron) qui apprend à combiner les sorties des 3 piliers :

  Entrées (vecteur de 9 features) :
  ┌─────────────────────────────────────────────────────────────────┐
  │ 1. prob_base        — Probabilité classe BASE    (Modèle 1 ML)  │
  │ 2. prob_sensitive   — Probabilité classe SENSITIVE              │
  │ 3. prob_critical    — Probabilité classe CRITICAL               │
  │ 4. risk_score_norm  — Score de risque normalisé [0,1]           │
  │ 5. anomaly_score_n  — Score Isolation Forest normalisé          │
  │ 6. is_anomalous     — Flag anomalie (0/1)                       │
  │ 7. anomaly_sev_num  — Sévérité anomalie encodée (0-4)           │
  │ 8. nlp_score_norm   — Score NLP normalisé [0,1]                 │
  │ 9. trust_score_norm — Trust Score employé normalisé [0,1]       │
  └─────────────────────────────────────────────────────────────────┘

  Sortie : vecteur softmax 3 classes → [P(BASE), P(SENSITIVE), P(CRITICAL)]

Architecture MLP :
  Input(9) → Dense(32, ReLU) → Dense(16, ReLU) → Dense(3, Softmax)

Le modèle est :
  1. Pré-entraîné avec des exemples synthétiques au démarrage (si pas de pkl).
  2. Fine-tuné en ligne (online learning) à chaque décision experte enregistrée.
  3. Sauvegardé dans models/nn_fusion_model.pkl

NOTE : On utilise scikit-learn (MLPClassifier) pour éviter une dépendance
       lourde à PyTorch/TensorFlow dans un contexte PFE.
"""

import os
import joblib
import numpy as np
from typing import Optional

# ─── Constantes ───────────────────────────────────────────────────────────────
LEVEL_TO_INT  = {"BASE": 0, "SENSITIVE": 1, "CRITICAL": 2}
INT_TO_LEVEL  = {0: "BASE",  1: "SENSITIVE",  2: "CRITICAL"}
SEV_TO_INT    = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
MODEL_PATH    = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "models", "nn_fusion_model.pkl"
)


class NNFusionEngine:
    """
    Moteur de décision par réseau de neurones.

    Peut fonctionner en deux modes :
    - MODE_NN   : Le MLP prédit la décision finale (mode actif si modèle chargé)
    - MODE_RULE : Fallback sur la logique à table si MLP indisponible
    """

    def __init__(self):
        self._model    = None  # MLPClassifier sklearn
        self._loaded   = False
        self._mode     = "RULE"  # "NN" ou "RULE"

    # ─────────────────────────────────────────────────────────────────────────
    # Chargement / Initialisation
    # ─────────────────────────────────────────────────────────────────────────

    def load_or_init(self):
        """Charge le modèle pkl OU initialise + pré-entraîne un nouveau."""
        if os.path.exists(MODEL_PATH):
            try:
                data = joblib.load(MODEL_PATH)
                if isinstance(data, dict):
                    self._model  = data["model"]
                    self._scaler = data["scaler"]
                else:
                    self._model  = data
                    # Si c'est un ancien format sans scaler, on risque une erreur plus tard
                    # mais on essaie de charger au moins le modèle.
                
                self._loaded = True
                self._mode   = "NN"
                print("INFO: NN Fusion Engine charge")
                return
            except Exception as e:
                print(f"WARNING: Impossible de charger nn_fusion_model.pkl : {e}")

        # Nouveau modèle → pré-entraînement synthétique
        print("INFO: NN Fusion Engine  pr-entranement sur donnes synthtiques...")
        self._pretrain()

    def _pretrain(self):
        """Pré-entraîne le MLP sur un historique massif simulé (15000 tickets)."""
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler

        X, y = self._generate_synthetic_data(n=15000)

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._model = MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
        )
        self._model.fit(X_scaled, y)
        self._loaded = True
        self._mode   = "NN"

        # Sauvegarder pour les prochains démarrages
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump({"model": self._model, "scaler": self._scaler}, MODEL_PATH)
        print(f"INFO: NN Fusion Engine pre-entraine et sauvegarde ({len(y)} exemples).")

    def _generate_synthetic_data(self, n: int = 15000):
        """
        Génère des exemples synthétiques simulant un historique ITSM massif.
        Chaque exemple représente un contexte de fusion réaliste.
        """
        rng = np.random.default_rng(42)
        X, y = [], []

        for _ in range(n):
            # ── Classe cible aléatoire ────────────────────────────────────
            label = rng.choice([0, 1, 2], p=[0.35, 0.40, 0.25])

            if label == 0:   # BASE
                prob_base   = rng.uniform(0.55, 0.95)
                prob_sens   = rng.uniform(0.03, 0.30)
                prob_crit   = max(0, 1 - prob_base - prob_sens)
                risk_norm   = rng.uniform(0.0, 0.30)
                anomaly_n   = rng.uniform(0.3, 1.0)   # peu anormal
                is_anom     = 0
                anom_sev    = 0
                nlp_norm    = rng.uniform(0.5, 1.0)
                trust_norm  = rng.uniform(0.55, 1.0)

            elif label == 1: # SENSITIVE
                prob_base   = rng.uniform(0.05, 0.45)
                prob_sens   = rng.uniform(0.40, 0.80)
                prob_crit   = max(0, 1 - prob_base - prob_sens)
                risk_norm   = rng.uniform(0.25, 0.60)
                anomaly_n   = rng.uniform(-0.2, 0.5)
                is_anom     = rng.choice([0, 1], p=[0.5, 0.5])
                anom_sev    = rng.choice([0, 1, 2]) if is_anom else 0
                nlp_norm    = rng.uniform(0.3, 0.7)
                trust_norm  = rng.uniform(0.35, 0.75)

            else:            # CRITICAL
                prob_base   = rng.uniform(0.0, 0.20)
                prob_sens   = rng.uniform(0.05, 0.40)
                prob_crit   = max(0, 1 - prob_base - prob_sens)
                risk_norm   = rng.uniform(0.50, 1.0)
                anomaly_n   = rng.uniform(-1.0, -0.1)
                is_anom     = rng.choice([0, 1], p=[0.2, 0.8])
                anom_sev    = rng.choice([2, 3, 4]) if is_anom else 0
                nlp_norm    = rng.uniform(0.0, 0.40)
                trust_norm  = rng.uniform(0.0, 0.50)

            # Normaliser anom_sev
            anom_sev_norm = anom_sev / 4.0

            X.append([
                max(0, min(1, prob_base)),
                max(0, min(1, prob_sens)),
                max(0, min(1, prob_crit)),
                max(0, min(1, risk_norm)),
                max(-1, min(1, anomaly_n)),
                float(is_anom),
                anom_sev_norm,
                max(0, min(1, nlp_norm)),
                max(0, min(1, trust_norm)),
            ])
            y.append(label)

        return np.array(X), np.array(y)

    # ─────────────────────────────────────────────────────────────────────────
    # Point d'entrée principal
    # ─────────────────────────────────────────────────────────────────────────

    def predict(
        self,
        model1_result: dict,
        anomaly_result: dict,
    ) -> dict:
        """
        Prédit la décision finale en fusionnant les sorties M1 + M2.

        Returns:
            dict avec :
              - final_level      : "BASE" | "SENSITIVE" | "CRITICAL"
              - nn_probabilities : {"BASE": 0.xx, "SENSITIVE": 0.xx, "CRITICAL": 0.xx}
              - nn_confidence    : float [0,1]
              - fusion_mode      : "NN" | "RULE"
              - risk_boost       : points ajoutés par l'anomalie
        """
        risk_boost      = anomaly_result.get("risk_boost", 0)
        anomaly_severity = anomaly_result.get("severity", "NONE")

        if self._loaded and self._mode == "NN":
            features = self._build_features(model1_result, anomaly_result)
            try:
                scaled = self._scaler.transform([features])
                proba  = self._model.predict_proba(scaled)[0]
                pred_idx = int(np.argmax(proba))
                final_level = INT_TO_LEVEL[pred_idx]
                nn_conf = float(np.max(proba))

                # ── Contrainte de sécurité : si M1=CRITICAL → jamais descendre ──
                m1_level = model1_result.get("level", "BASE")
                if m1_level == "CRITICAL":
                    final_level = "CRITICAL"

                return {
                    "final_level":       final_level,
                    "nn_probabilities":  {
                        "BASE":      round(float(proba[0]), 4),
                        "SENSITIVE": round(float(proba[1]), 4),
                        "CRITICAL":  round(float(proba[2]), 4),
                    },
                    "nn_confidence":     nn_conf,
                    "fusion_mode":       "NN",
                    "risk_boost":        risk_boost,
                    "anomaly_severity":  anomaly_severity,
                }
            except Exception as e:
                print(f"WARNING: NN fusion error ({e})  fallback rgles")

        # ── Fallback : logique à table ───────────────────────────────────────
        return self._rule_fallback(model1_result, anomaly_result)

    def _rule_fallback(self, m1: dict, m2: dict) -> dict:
        """Logique de fusion déterministe (backup si NN indisponible)."""
        ANOMALY_MIN_LEVEL = {"NONE": "BASE", "LOW": "SENSITIVE", "MEDIUM": "SENSITIVE", "HIGH": "CRITICAL", "CRITICAL": "CRITICAL"}
        LEVEL_ORDER = {"BASE": 0, "SENSITIVE": 1, "CRITICAL": 2}
        m1_level = m1.get("level", "BASE")
        sev      = m2.get("severity", "NONE")
        m2_min   = ANOMALY_MIN_LEVEL.get(sev, "BASE")
        final    = m1_level if LEVEL_ORDER.get(m1_level, 0) >= LEVEL_ORDER.get(m2_min, 0) else m2_min
        return {
            "final_level":      final,
            "nn_probabilities": {final: 1.0},
            "nn_confidence":    0.7,
            "fusion_mode":      "RULE",
            "risk_boost":       m2.get("risk_boost", 0),
            "anomaly_severity": sev,
        }

    def _build_features(self, m1: dict, m2: dict) -> list:
        """Construit le vecteur de features d'entrée du MLP."""
        probs = m1.get("probabilities", {})
        if isinstance(probs, dict):
            # Probabilities sont en % (ex: 85.0) → normaliser en [0,1]
            prob_base  = probs.get("BASE", 0) / 100.0
            prob_sens  = probs.get("SENSITIVE", 0) / 100.0
            prob_crit  = probs.get("CRITICAL", 0) / 100.0
        else:
            prob_base, prob_sens, prob_crit = 0.33, 0.33, 0.33

        risk_score  = m1.get("risk_score_rules", m1.get("risk_score", 0))
        risk_norm   = max(0.0, min(1.0, risk_score / 200.0))

        anomaly_score = m2.get("anomaly_score")
        anomaly_n   = float(anomaly_score) if anomaly_score is not None else 0.5
        anomaly_n   = max(-1.0, min(1.0, anomaly_n))

        is_anom     = 1.0 if m2.get("is_anomalous", False) else 0.0
        sev_num     = SEV_TO_INT.get(m2.get("severity", "NONE"), 0) / 4.0

        nlp_score   = m1.get("nlp_score", 50)
        nlp_norm    = max(0.0, min(1.0, float(nlp_score) / 100.0))

        trust_score = m1.get("trust_score")
        trust_norm  = max(0.0, min(1.0, float(trust_score) / 100.0)) if trust_score is not None else 0.5

        return [prob_base, prob_sens, prob_crit, risk_norm, anomaly_n, is_anom, sev_num, nlp_norm, trust_norm]

    # ─────────────────────────────────────────────────────────────────────────
    # Online Learning — Apprentissage depuis les corrections expertes
    # ─────────────────────────────────────────────────────────────────────────

    def learn_from_expert(self, m1_result: dict, m2_result: dict, expert_level: str):
        """
        Met à jour le MLP avec une correction experte (active learning).
        Appelé après chaque approbation/rejet manuel par un admin.
        """
        if not self._loaded or expert_level not in LEVEL_TO_INT:
            return False
        try:
            features = self._build_features(m1_result, m2_result)
            X = self._scaler.transform([features])
            y = [LEVEL_TO_INT[expert_level]]
            self._model.partial_fit(X, y, classes=[0, 1, 2])
            joblib.dump({"model": self._model, "scaler": self._scaler}, MODEL_PATH)
            print(f"INFO: NN Fusion -- apprentissage depuis expert ({expert_level})")
            return True
        except Exception as e:
            print(f"WARNING: NN learn_from_expert error : {e}")
            return False


# ── Singleton ─────────────────────────────────────────────────────────────────
nn_fusion_engine = NNFusionEngine()