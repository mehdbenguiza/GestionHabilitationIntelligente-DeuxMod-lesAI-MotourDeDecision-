# Rapport de Comparaison des Modèles ML
**Projet** : Gestion Intelligente des Habilitations — PFE BIAT  
**Date** : 31/05/2026 à 19:47  
**Dataset** : 5242 tickets d'entraînement  

---

## Résumé Exécutif

Cinq algorithmes de Machine Learning ont été évalués sur un jeu de données de **5242 tickets d'habilitation bancaire** (Split 80/20, Validation Croisée 5-Fold).

**Le modèle le plus performant est : 🏆 Gradient Boosting**

| Métrique | Résultat |
|---|---|
| Accuracy | **89.04%** |
| F1-Score Macro | **87.64%** |
| Validation Croisée 5-Fold | **89.83%** |

---

## Tableau Comparatif Complet

| Rang | Modèle | Accuracy | F1 Macro | F1 Weighted | Précision | Rappel | CV 5-Fold | Train (s) | Inférence (ms) |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 🥇 **Gradient Boosting** | 89.04% | 87.64% | 89.02% | 87.76% | 87.53% | 89.83% (±0.73%) | 2.207s | 13.42ms |
| 2 | 🥈 **XGBoost** | 88.75% | 87.54% | 88.77% | 87.71% | 87.39% | 90.1% (±0.84%) | 2.406s | 8.98ms |
| 3 | 🥉 **Random Forest (v2.0)** | 85.03% | 83.98% | 85.12% | 84.42% | 83.64% | 85.25% (±1.49%) | 0.388s | 18.11ms |
| 4 |    **Decision Tree** | 81.79% | 81.04% | 82.08% | 80.9% | 81.46% | 83.33% (±0.98%) | 0.016s | 1.89ms |
| 5 |    **Réseau de Neurones (MLP)** | 78.65% | 76.66% | 78.46% | 77.93% | 75.7% | 81.53% (±1.6%) | 0.97s | 2.42ms |

---

## Rapport de Classification Détaillé — Gradient Boosting

| Classe | Précision | Rappel | F1-Score | Support |
|---|:---:|:---:|:---:|:---:|
| **BASE** | 93.57% | 94.29% | 93.93% | 525 |
| **CRITICAL** | 89.36% | 88.24% | 88.79% | 238 |
| **SENSITIVE** | 80.35% | 80.07% | 80.21% | 286 |
| **Avg Weighted** | 89.01% | 89.04% | 89.02% | 1049 |

---

## Analyse & Justification du Choix

### Decision Tree — Rang #4

**Points forts** : Interprétable, très rapide.  
**Points faibles** : Sujet au sur-apprentissage (overfitting), performances limitées sur des données complexes.  
**Rôle dans cette étude** : Modèle de base (baseline) servant de référence.

### Random Forest (v2.0) — Rang #3

**Points forts** : Robuste, insensible au bruit, gère bien les données déséquilibrées.  
**Points faibles** : Plus lent en inférence, moins précis que le Boosting.  
**Rôle dans cette étude** : Modèle actuel de production (v2.0), très fiable.

### Gradient Boosting — Rang #1

**Points forts** : Apprentissage séquentiel qui corrige ses propres erreurs, très précis.  
**Points faibles** : Lent à entraîner, sensible au learning_rate.  
**Rôle dans cette étude** : Challenger du Random Forest.

### XGBoost — Rang #2

**Points forts** : Régularisation intégrée (évite l'overfitting), très rapide, champion des compétitions Kaggle.  
**Points faibles** : Nombreux hyperparamètres à régler.  
**Rôle dans cette étude** : Candidat principal pour la V3.0.

### Réseau de Neurones (MLP) — Rang #5

**Points forts** : Capture des relations très complexes et non-linéaires.  
**Points faibles** : Nécessite beaucoup de données, temps d'entraînement élevé, résultats souvent inférieurs aux Boosting sur des données tabulaires.  
**Rôle dans cette étude** : Alternative Deep Learning.

---

## Recommandation Finale

> 🏆 **Modèle recommandé pour la V3.0 : Gradient Boosting**

Sur la base de l'évaluation objective des 5 modèles, **Gradient Boosting** obtient les meilleurs résultats avec un F1-Score Macro de **87.64%** et une Accuracy de **89.04%**, confirmée par une Validation Croisée 5-Fold à **89.83%**.

Ce modèle sera intégré au moteur hybride (ML + Règles Métier) de la plateforme de Gestion des Habilitations BIAT, remplaçant le Random Forest (v2.0) pour offrir une classification plus robuste et des faux positifs réduits sur les tickets de niveau CRITIQUE.

---

*Rapport généré automatiquement le 31/05/2026 à 19:47 par le script `compare_models.py`*
