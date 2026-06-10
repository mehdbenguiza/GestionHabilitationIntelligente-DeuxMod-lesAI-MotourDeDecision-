# scripts/compare_models.py
"""
╔══════════════════════════════════════════════════════════════╗
║   COMPARAISON DES 5 MODELES ML - PFE Gestion Habilitations  ║
║   ✅ 100% SAFE : Ne touche PAS au modèle existant (.pkl)    ║
╚══════════════════════════════════════════════════════════════╝

Ce script compare :
  1. Decision Tree          (Baseline)
  2. Random Forest          (Modèle actuel v2.0)
  3. Gradient Boosting      (Challenger)
  4. XGBoost                (State-of-the-art)
  5. Réseau de Neurones MLP (Deep Learning)

Et génère :
  - Un tableau comparatif dans la console
  - Un rapport HTML/Markdown dans : reports/model_comparison_report.md
  - Des graphiques de comparaison (si matplotlib installé)

Usage :
    cd d:\\ProjetPFE\\Backend
    python scripts/compare_models.py
"""

import os
import sys
import time
import warnings
warnings.filterwarnings("ignore")

# ── Encoding UTF-8 (Windows) ────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Modèles ML ──────────────────────────────────────────────────────────────
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, accuracy_score, f1_score,
    precision_score, recall_score, confusion_matrix
)

# ── XGBoost (optionnel si pas installé) ──────────────────────────────────────
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost non installé. Installation : pip install xgboost")
    print("    (Le script continuera sans XGBoost)")

from app.services.feature_extractor import FeatureExtractor

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

DATA_DIR    = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
CSV_PATH    = os.path.join(DATA_DIR, "training_dataset.csv")

os.makedirs(REPORTS_DIR, exist_ok=True)

SEPARATOR = "=" * 70

# ═══════════════════════════════════════════════════════════════════════════
# 1. CHARGEMENT DES DONNÉES
# ═══════════════════════════════════════════════════════════════════════════

print(f"\n{SEPARATOR}")
print("  COMPARAISON DE 5 MODELES ML - Gestion des Habilitations BIAT")
print(f"{SEPARATOR}")
print(f"  Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"{SEPARATOR}\n")

if not os.path.exists(CSV_PATH):
    print(f"❌ ERREUR : Dataset introuvable à : {CSV_PATH}")
    print("   Lancez d'abord : python scripts/generate_training_data.py")
    sys.exit(1)

print("📂 Chargement du dataset...")
df = pd.read_csv(CSV_PATH)
print(f"   ✅ {len(df)} tickets chargés")
print(f"   📊 Distribution des labels :")
print(df["label"].value_counts().to_string(header=False))

# ═══════════════════════════════════════════════════════════════════════════
# 2. PRÉPARATION DES FEATURES (Réutilise ton FeatureExtractor existant)
# ═══════════════════════════════════════════════════════════════════════════

print("\n🔧 Préparation des features avec ton FeatureExtractor...")
extractor = FeatureExtractor()
extractor.fit(df)
X = extractor.transform(df)
y = df["label"]

# Encodage numérique des labels pour XGBoost et MLP
from sklearn.preprocessing import LabelEncoder
le_label = LabelEncoder()
y_encoded = le_label.fit_transform(y)

print(f"   ✅ {X.shape[1]} features extraites")

# Split Train/Test (même split pour tous les modèles = comparaison équitable)
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"   ✅ Train : {len(X_train)} | Test : {len(X_test)}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. DÉFINITION DES 5 MODÈLES
# ═══════════════════════════════════════════════════════════════════════════

models = {
    "Decision Tree": DecisionTreeClassifier(
        max_depth=15,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
    ),
    "Random Forest (v2.0)": RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        random_state=42,
    ),
    "Réseau de Neurones (MLP)": MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        solver="adam",
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        random_state=42,
    ),
}

if XGBOOST_AVAILABLE:
    n_classes = len(le_label.classes_)
    models["XGBoost"] = XGBClassifier(
        n_estimators=200,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        num_class=n_classes,
        random_state=42,
        verbosity=0,
    )

# ═══════════════════════════════════════════════════════════════════════════
# 4. ENTRAÎNEMENT ET ÉVALUATION DE CHAQUE MODÈLE
# ═══════════════════════════════════════════════════════════════════════════

print(f"\n{SEPARATOR}")
print("  ENTRAÎNEMENT ET ÉVALUATION")
print(f"{SEPARATOR}")

results = []
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for model_name, model in models.items():
    print(f"\n🤖 [{model_name}]")
    print(f"   Entraînement en cours...", end=" ", flush=True)

    # Mesure du temps d'entraînement
    t_start = time.time()
    model.fit(X_train, y_train)
    train_time = round(time.time() - t_start, 3)

    # Prédiction Test
    t_infer = time.time()
    y_pred = model.predict(X_test)
    infer_time_ms = round((time.time() - t_infer) * 1000, 2)

    # Métriques
    accuracy    = round(accuracy_score(y_test, y_pred) * 100, 2)
    f1_macro    = round(f1_score(y_test, y_pred, average="macro") * 100, 2)
    f1_weighted = round(f1_score(y_test, y_pred, average="weighted") * 100, 2)
    precision   = round(precision_score(y_test, y_pred, average="macro") * 100, 2)
    recall      = round(recall_score(y_test, y_pred, average="macro") * 100, 2)

    # Cross-Validation 5-Fold sur tout le dataset
    cv_scores = cross_val_score(model, X, y_encoded, cv=cv, scoring="accuracy")
    cv_mean   = round(cv_scores.mean() * 100, 2)
    cv_std    = round(cv_scores.std() * 100, 2)

    print(f"✅ Done !")
    print(f"   Accuracy       : {accuracy}%")
    print(f"   F1-Score Macro : {f1_macro}%")
    print(f"   CV 5-Fold      : {cv_mean}% (±{cv_std}%)")
    print(f"   Temps Train    : {train_time}s | Inférence : {infer_time_ms}ms")

    results.append({
        "Modèle":              model_name,
        "Accuracy (%)":        accuracy,
        "F1-Score Macro (%)":  f1_macro,
        "F1-Score Weighted (%)": f1_weighted,
        "Précision Macro (%)": precision,
        "Rappel Macro (%)":    recall,
        "CV 5-Fold (%)":       cv_mean,
        "CV Écart-Type (%)":   cv_std,
        "Temps Train (s)":     train_time,
        "Inférence (ms)":      infer_time_ms,
        "_model_obj":          model,
    })

# ═══════════════════════════════════════════════════════════════════════════
# 5. TABLEAU COMPARATIF CONSOLE
# ═══════════════════════════════════════════════════════════════════════════

df_results = pd.DataFrame(results).drop(columns=["_model_obj"])

# Trier par F1-Score Macro décroissant
df_sorted = df_results.sort_values("F1-Score Macro (%)", ascending=False).reset_index(drop=True)
df_sorted.index = df_sorted.index + 1  # Commencer à 1

print(f"\n\n{SEPARATOR}")
print("  TABLEAU COMPARATIF DES MODÈLES")
print(f"{SEPARATOR}\n")

# Affichage formaté
cols_display = [
    "Modèle", "Accuracy (%)", "F1-Score Macro (%)", "Précision Macro (%)",
    "Rappel Macro (%)", "CV 5-Fold (%)", "Temps Train (s)"
]
print(df_sorted[cols_display].to_string(index=True))

# ── Vainqueur ────────────────────────────────────────────────────────────────
winner = df_sorted.iloc[0]["Modèle"]
winner_acc = df_sorted.iloc[0]["Accuracy (%)"]
winner_f1  = df_sorted.iloc[0]["F1-Score Macro (%)"]
winner_cv  = df_sorted.iloc[0]["CV 5-Fold (%)"]

print(f"\n{'─' * 70}")
print(f"  🏆 GAGNANT : {winner}")
print(f"       Accuracy    : {winner_acc}%")
print(f"       F1 Macro    : {winner_f1}%")
print(f"       CV 5-Fold   : {winner_cv}%")
print(f"{'─' * 70}")

# ═══════════════════════════════════════════════════════════════════════════
# 6. RAPPORT MARKDOWN DÉTAILLÉ
# ═══════════════════════════════════════════════════════════════════════════

report_path = os.path.join(REPORTS_DIR, "model_comparison_report.md")

label_names = le_label.classes_.tolist()

# Récupérer le meilleur modèle pour le rapport détaillé
best_model_obj = None
for r in results:
    if r["Modèle"] == winner:
        best_model_obj = r["_model_obj"]
        break

with open(report_path, "w", encoding="utf-8") as f:
    f.write("# Rapport de Comparaison des Modèles ML\n")
    f.write(f"**Projet** : Gestion Intelligente des Habilitations — PFE BIAT  \n")
    f.write(f"**Date** : {datetime.now().strftime('%d/%m/%Y à %H:%M')}  \n")
    f.write(f"**Dataset** : {len(df)} tickets d'entraînement  \n\n")
    f.write("---\n\n")

    # ── Résumé exécutif ─────────────────────────────────────────────────────
    f.write("## Résumé Exécutif\n\n")
    f.write(f"Cinq algorithmes de Machine Learning ont été évalués sur un jeu de données ")
    f.write(f"de **{len(df)} tickets d'habilitation bancaire** (Split 80/20, Validation Croisée 5-Fold).\n\n")
    f.write(f"**Le modèle le plus performant est : 🏆 {winner}**\n\n")
    f.write(f"| Métrique | Résultat |\n")
    f.write(f"|---|---|\n")
    f.write(f"| Accuracy | **{winner_acc}%** |\n")
    f.write(f"| F1-Score Macro | **{winner_f1}%** |\n")
    f.write(f"| Validation Croisée 5-Fold | **{winner_cv}%** |\n\n")
    f.write("---\n\n")

    # ── Tableau comparatif complet ───────────────────────────────────────────
    f.write("## Tableau Comparatif Complet\n\n")
    f.write("| Rang | Modèle | Accuracy | F1 Macro | F1 Weighted | Précision | Rappel | CV 5-Fold | Train (s) | Inférence (ms) |\n")
    f.write("|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    for rank, row in df_sorted.iterrows():
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
        f.write(
            f"| {rank} | {medal} **{row['Modèle']}** | {row['Accuracy (%)']}% | "
            f"{row['F1-Score Macro (%)']}% | {row['F1-Score Weighted (%)']}% | "
            f"{row['Précision Macro (%)']}% | {row['Rappel Macro (%)']}% | "
            f"{row['CV 5-Fold (%)']}% (±{row['CV Écart-Type (%)']}%) | "
            f"{row['Temps Train (s)']}s | {row['Inférence (ms)']}ms |\n"
        )

    f.write("\n---\n\n")

    # ── Classification Report du gagnant ─────────────────────────────────────
    f.write(f"## Rapport de Classification Détaillé — {winner}\n\n")
    if best_model_obj:
        y_pred_best = best_model_obj.predict(X_test)
        report = classification_report(
            y_test, y_pred_best,
            target_names=label_names,
            output_dict=True
        )
        f.write("| Classe | Précision | Rappel | F1-Score | Support |\n")
        f.write("|---|:---:|:---:|:---:|:---:|\n")
        for cls in label_names:
            r = report[cls]
            f.write(
                f"| **{cls}** | {r['precision']:.2%} | {r['recall']:.2%} | "
                f"{r['f1-score']:.2%} | {int(r['support'])} |\n"
            )
        f.write(f"| **Avg Weighted** | {report['weighted avg']['precision']:.2%} | "
                f"{report['weighted avg']['recall']:.2%} | "
                f"{report['weighted avg']['f1-score']:.2%} | {int(report['weighted avg']['support'])} |\n")

    f.write("\n---\n\n")

    # ── Analyse & Recommandation ─────────────────────────────────────────────
    f.write("## Analyse & Justification du Choix\n\n")

    analyses = {
        "Decision Tree": (
            "**Points forts** : Interprétable, très rapide.  \n"
            "**Points faibles** : Sujet au sur-apprentissage (overfitting), "
            "performances limitées sur des données complexes.  \n"
            "**Rôle dans cette étude** : Modèle de base (baseline) servant de référence."
        ),
        "Random Forest (v2.0)": (
            "**Points forts** : Robuste, insensible au bruit, gère bien les données déséquilibrées.  \n"
            "**Points faibles** : Plus lent en inférence, moins précis que le Boosting.  \n"
            "**Rôle dans cette étude** : Modèle actuel de production (v2.0), très fiable."
        ),
        "Gradient Boosting": (
            "**Points forts** : Apprentissage séquentiel qui corrige ses propres erreurs, très précis.  \n"
            "**Points faibles** : Lent à entraîner, sensible au learning_rate.  \n"
            "**Rôle dans cette étude** : Challenger du Random Forest."
        ),
        "XGBoost": (
            "**Points forts** : Régularisation intégrée (évite l'overfitting), très rapide, "
            "champion des compétitions Kaggle.  \n"
            "**Points faibles** : Nombreux hyperparamètres à régler.  \n"
            "**Rôle dans cette étude** : Candidat principal pour la V3.0."
        ),
        "Réseau de Neurones (MLP)": (
            "**Points forts** : Capture des relations très complexes et non-linéaires.  \n"
            "**Points faibles** : Nécessite beaucoup de données, temps d'entraînement élevé, "
            "résultats souvent inférieurs aux Boosting sur des données tabulaires.  \n"
            "**Rôle dans cette étude** : Alternative Deep Learning."
        ),
    }

    for model_name, analysis in analyses.items():
        if model_name in df_results["Modèle"].values or model_name.split(" (")[0] in [r["Modèle"].split(" (")[0] for r in results]:
            row_data = df_results[df_results["Modèle"] == model_name]
            if row_data.empty:
                continue
            rank = df_sorted[df_sorted["Modèle"] == model_name].index.tolist()
            rank_str = f"Rang #{rank[0]}" if rank else ""
            f.write(f"### {model_name} — {rank_str}\n\n")
            f.write(analysis + "\n\n")

    f.write("---\n\n")

    # ── Recommandation finale ─────────────────────────────────────────────────
    f.write("## Recommandation Finale\n\n")
    f.write(f"> 🏆 **Modèle recommandé pour la V3.0 : {winner}**\n\n")
    f.write(
        f"Sur la base de l'évaluation objective des 5 modèles, **{winner}** "
        f"obtient les meilleurs résultats avec un F1-Score Macro de **{winner_f1}%** "
        f"et une Accuracy de **{winner_acc}%**, confirmée par une Validation Croisée 5-Fold "
        f"à **{winner_cv}%**.\n\n"
    )
    f.write(
        "Ce modèle sera intégré au moteur hybride (ML + Règles Métier) de la plateforme "
        "de Gestion des Habilitations BIAT, remplaçant le Random Forest (v2.0) "
        "pour offrir une classification plus robuste et des faux positifs réduits "
        "sur les tickets de niveau CRITIQUE.\n\n"
    )
    f.write("---\n\n")
    f.write(f"*Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')} "
            f"par le script `compare_models.py`*\n")

print(f"\n\n{'=' * 70}")
print(f"  ✅ RAPPORT COMPLET SAUVEGARDÉ :")
print(f"     {report_path}")
print(f"{'=' * 70}")

# ═══════════════════════════════════════════════════════════════════════════
# 7. GRAPHIQUES (optionnel)
# ═══════════════════════════════════════════════════════════════════════════

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Comparaison des Modèles ML — Gestion des Habilitations BIAT", fontsize=14, fontweight="bold")

    models_names = df_sorted["Modèle"].tolist()
    colors       = ["#FFD700", "#C0C0C0", "#CD7F32", "#4169E1", "#DC143C"][:len(models_names)]

    # Graphique 1 : F1-Score Macro
    ax1 = axes[0]
    bars1 = ax1.barh(models_names, df_sorted["F1-Score Macro (%)"].tolist(), color=colors, edgecolor="white")
    ax1.set_title("F1-Score Macro (%)", fontweight="bold")
    ax1.set_xlim(0, 105)
    for bar, val in zip(bars1, df_sorted["F1-Score Macro (%)"].tolist()):
        ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f"{val}%",
                 va='center', fontweight="bold", fontsize=10)
    ax1.invert_yaxis()
    ax1.grid(axis="x", alpha=0.3)

    # Graphique 2 : Accuracy vs CV
    ax2 = axes[1]
    x = np.arange(len(models_names))
    width = 0.35
    bars2a = ax2.bar(x - width/2, df_sorted["Accuracy (%)"].tolist(), width, label="Accuracy", color="#003087", alpha=0.85)
    bars2b = ax2.bar(x + width/2, df_sorted["CV 5-Fold (%)"].tolist(), width, label="CV 5-Fold", color="#10B981", alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels([m.replace(" (v2.0)", "").replace(" (MLP)", "").replace("Réseau de Neurones", "MLP") for m in models_names], rotation=15, ha="right")
    ax2.set_ylim(0, 110)
    ax2.set_title("Accuracy vs Cross-Validation (%)", fontweight="bold")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    chart_path = os.path.join(REPORTS_DIR, "model_comparison_chart.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    print(f"  📊 Graphique sauvegardé : {chart_path}")
except ImportError:
    print("  ℹ️  matplotlib non installé — graphiques ignorés.")
    print("     Pour les activer : pip install matplotlib")

print(f"\n  🚀 Analyse terminée ! Ouvre le rapport dans :")
print(f"     {report_path}")
print()
