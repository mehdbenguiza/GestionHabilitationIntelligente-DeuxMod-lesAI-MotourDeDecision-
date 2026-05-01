# Système de Gestion Intelligente des Habilitations IT

[![🔬 Backend CI](https://github.com/mehdbenguiza/GestionHabilitationIntelligente-DeuxMod-lesAI-MotourDeDecision-/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/mehdbenguiza/GestionHabilitationIntelligente-DeuxMod-lesAI-MotourDeDecision-/actions/workflows/backend-ci.yml)
[![🎨 Frontend CI](https://github.com/mehdbenguiza/GestionHabilitationIntelligente-DeuxMod-lesAI-MotourDeDecision-/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/mehdbenguiza/GestionHabilitationIntelligente-DeuxMod-lesAI-MotourDeDecision-/actions/workflows/frontend-ci.yml)

> **Projet de Fin d'Études — BIAT 2026**  
> Système intelligent de gestion des habilitations d'accès aux systèmes d'information,
> intégrant des modèles IA (Random Forest, XGBoost, SHAP) pour la classification
> automatique des tickets et l'évaluation du risque.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Frontend React + Vite + TypeScript  │  :5173 (dev) / :80 (Docker)
│  MUI + Radix UI + Recharts           │
└────────────────┬────────────────────┘
                 │ REST API
┌────────────────▼────────────────────┐
│  Backend FastAPI (Python 3.11)       │  :8000
│  SQLAlchemy · JWT · Pytest           │
│  Random Forest · XGBoost · SHAP      │
└─────────────────────────────────────┘
```

---

## 🚀 Lancement rapide

### Option 1 — Développement local (habituel)

```bash
# Backend
cd Backend
.\venv\Scripts\activate          # Windows
python run.py                    # → http://localhost:8000

# Frontend (dans un autre terminal)
cd FrontendPFE
npm run dev                      # → http://localhost:5173
```

### Option 2 — Docker (toute la stack en une commande)

```bash
# Prérequis : Docker Desktop installé

# Copier et remplir les secrets
cp .env.example .env

# Lancer
docker-compose up --build

# Accès
# Frontend → http://localhost:80
# Backend  → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

---

## 🧪 Tests

```bash
cd Backend
.\venv\Scripts\activate
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Modules de tests :**
| Fichier | Ce qui est testé |
|---|---|
| `test_01_health.py` | Santé de l'API (`/` et `/health`) |
| `test_02_auth.py` | Authentification JWT |
| `test_03_create_user.py` | Création d'utilisateurs |
| `test_04_tickets.py` | CRUD des tickets |
| `test_05_ai_classify.py` | Classification IA (BASE/SENSITIVE/CRITIQUE) |
| `test_06_notifications.py` | Système de notifications |

---

## ⚙️ CI/CD (GitHub Actions)

À chaque `git push`, deux pipelines s'exécutent automatiquement :

| Pipeline | Déclencheur | Étapes |
|---|---|---|
| **Backend CI** | Modification dans `Backend/**` | Lint → Tests Pytest → Docker Build |
| **Frontend CI** | Modification dans `FrontendPFE/**` | npm Build → Docker Build |

---

## 🛠️ Stack technique

| Couche | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, TailwindCSS, MUI, Radix UI |
| **Backend** | FastAPI, SQLAlchemy, Pydantic v2, Uvicorn |
| **IA / ML** | scikit-learn, XGBoost, SHAP, pandas, numpy |
| **Sécurité** | JWT (python-jose), bcrypt, MFA, Zero Trust JIT |
| **Tests** | Pytest, pytest-cov, pytest-asyncio |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
