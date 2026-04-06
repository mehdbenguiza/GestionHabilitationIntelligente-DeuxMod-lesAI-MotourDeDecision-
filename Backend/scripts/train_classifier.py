# scripts/train_classifier.py

import pandas as pd
import numpy as np
import os
import sys

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

from app.services.feature_extractor import FeatureExtractor

# ==================== CHARGEMENT DES DONNÉES ====================

print("="*50)
print("🎯 ENTRAÎNEMENT DU MODÈLE DE CLASSIFICATION")
print("="*50)

# Charger le dataset
data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "training_dataset.csv")
df = pd.read_csv(data_path)
print(f"\n📂 Dataset chargé : {len(df)} tickets")

# ==================== PRÉPARATION DES FEATURES ====================

print("\n🔧 Préparation des features...")

# Initialiser et entraîner l'extracteur de features
extractor = FeatureExtractor()
extractor.fit(df)

# Transformer les données
X = extractor.transform(df)
y = df['label']

print(f"\n📊 Features : {X.shape[1]} colonnes")
print(f"📊 Labels : {y.nunique()} classes ({y.unique().tolist()})")

# ==================== SPLIT TRAIN/TEST ====================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n📊 Split des données :")
print(f"   → Entraînement : {len(X_train)} tickets")
print(f"   → Test : {len(X_test)} tickets")

# ==================== ENTRAÎNEMENT ====================

print("\n🚀 Entraînement du modèle Random Forest...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'  # Compense le déséquilibre des classes
)

model.fit(X_train, y_train)

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

# Validation croisée
print("\n📊 Validation croisée (5 folds) :")
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"   → Scores : {cv_scores}")
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

# Sauvegarder l'extracteur
extractor.save("models/feature_extractor.pkl")

# Sauvegarder le modèle
model_path = "models/classifier_model.pkl"
joblib.dump(model, model_path)
print(f"✅ Modèle sauvegardé : {model_path}")

# Sauvegarder les métriques
metrics = {
    'accuracy': accuracy,
    'cv_mean': cv_scores.mean(),
    'cv_std': cv_scores.std(),
    'feature_importance': feature_importance.to_dict()
}
joblib.dump(metrics, "models/model_metrics.pkl")

print("\n✅ Script terminé avec succès !")
print(f"📁 Modèle : {model_path}")
print(f"📁 Extracteur : models/feature_extractor.pkl")