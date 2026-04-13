# scripts/train_classifier.py

import pandas as pd
import numpy as np
import os
import sys

# Ajouter le chemin du projet
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

from app.services.feature_extractor import FeatureExtractor

# ==================== CHARGEMENT DES DONNÉES ====================

print("="*50)
print("🎯 ENTRAÎNEMENT DU MODÈLE DE CLASSIFICATION")
print("="*50)

# 1. Charger le dataset généré (Bootstrap)
data_path = os.path.join(project_dir, "data", "training_dataset.csv")
df_generated = pd.read_csv(data_path)
df_generated['sample_weight'] = 1  # Poids basique

# 2. Charger le dataset manuel expert (Excel)
excel_path = os.path.join(project_dir, "datasetExcel", "dataset_tickets_realistic.xlsx")
try:
    df_manual = pd.read_excel(excel_path)
    # L'humain a raison : on donne un poids massif à ce dataset (ex: x15)
    df_manual['sample_weight'] = 15
    print(f"\n✅ Dataset EXPERT chargé : {len(df_manual)} tickets")
    df = pd.concat([df_generated, df_manual], ignore_index=True)
except Exception as e:
    print(f"\n⚠️ Impossible de charger le dataset Excel expert ({e}).")
    print("Utilisation du dataset généré uniquement.")
    df = df_generated

print(f"\n📂 Dataset total : {len(df)} tickets")

# ==================== PRÉPARATION DES FEATURES ====================

print("\n🔧 Préparation des features...")

# Initialiser et entraîner l'extracteur de features
extractor = FeatureExtractor()
extractor.fit(df)

# Transformer les données
X = extractor.transform(df)
y = df['label']
weights = df['sample_weight'].values

print(f"\n📊 Features : {X.shape[1]} colonnes")
print(f"📊 Labels : {y.nunique()} classes ({y.unique().tolist()})")

# ==================== SPLIT TRAIN/TEST ====================

X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
    X, y, weights, test_size=0.2, random_state=42, stratify=y
)

print(f"\n📊 Split des données :")
print(f"   → Entraînement : {len(X_train)} tickets")
print(f"   → Test : {len(X_test)} tickets")

# ==================== ENTRAÎNEMENT ====================

print("\n🚀 Entraînement du modèle Random Forest (avec Poids Experts)...")

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight='balanced'
)

# On force l'arbre à accorder plus d'importance aux tickets manuels
model.fit(X_train, y_train, sample_weight=w_train)

print("✅ Modèle entraîné avec succès !")

# ==================== ÉVALUATION ====================

print("\n📊 ÉVALUATION DU MODÈLE")
print("-"*30)

# Prédictions
y_pred = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"🎯 Accuracy : {accuracy:.2%}")

# Classification report
print("\n📋 Classification Report :")
print(classification_report(y_test, y_pred))

# Matrice de confusion
print("\n📊 Matrice de confusion :")
print(confusion_matrix(y_test, y_pred))

# Validation croisée sans poids pour voir les stats brutes
print("\n📊 Validation croisée (5 folds) :")
# Attention, cross_val_score ne supporte pas nativement sample_weight facilement avec cv=5
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"   → Moyenne : {cv_scores.mean():.2%}")
print(f"   → Écart-type : {cv_scores.std():.2%}")

# ==================== IMPORTANCE DES FEATURES ====================

print("\n📊 TOP 10 FEATURES LES PLUS IMPORTANTES :")
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False).head(10)

for i, row in feature_importance.iterrows():
    print(f"   → {row['feature']}: {row['importance']:.4f}")

# ==================== SAUVEGARDE ====================

print("\n💾 Sauvegarde des modèles...")

models_dir = os.path.join(project_dir, "models")
os.makedirs(models_dir, exist_ok=True)

# Sauvegarder l'extracteur
extractor_path = os.path.join(models_dir, "feature_extractor.pkl")
extractor.save(extractor_path)

# Sauvegarder le modèle
model_path = os.path.join(models_dir, "classifier_model.pkl")
joblib.dump(model, model_path)
print(f"✅ Modèle sauvegardé : {model_path}")

# Sauvegarder les métriques
metrics = {
    'accuracy': accuracy,
    'cv_mean': cv_scores.mean(),
    'cv_std': cv_scores.std(),
    'feature_importance': feature_importance.to_dict()
}
joblib.dump(metrics, os.path.join(models_dir, "model_metrics.pkl"))

print("\n✅ Script terminé avec succès !")
print(f"📁 Modèle : {model_path}")
print(f"📁 Extracteur : {extractor_path}")