from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from contextlib import asynccontextmanager
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.tickets import router as tickets_router
from app.api.endpoints.feedback import router as feedback_router
from app.api.endpoints.employees import router as employees_router
from app.api.endpoints.systemes import router as systemes_router
from app.api.endpoints.profiles import router as profiles_router
from app.database import engine, Base
from datetime import datetime, timezone
from app.api.endpoints.ai import router as ai_router
from app.api.endpoints.notifications import router as notifications_router
from app.api.endpoints.audit import router as audit_router
from app.api.endpoints.employee_portal import router as portal_router
from app.api.endpoints.automation_rules import router as automation_rules_router
from app.services.ai_service import ai_service
# Imports des modèles pour forcer la création des tables
import app.models.notification
import app.models.classification_result
import app.models.decision_engine
import app.models.audit_log
import app.models.employee
import app.models.ai_feedback   # ← Nouveau : feedback + corrections
import app.models.systeme        # ← Nouveau : référentiel systèmes SI
import app.models.access_profile # ← Nouveau : profils d'accès habilitations
import app.models.anomaly_log    # ← Modèle 2 : table anomaly_logs
import app.models.automation_rule




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application (remplace @on_event)"""
    # 1. Création des tables DB avec retry
    print("[STARTUP] Initialisation de la base de donnees...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[STARTUP] Tables DB verifiees/creees avec succes")
    except Exception as db_err:
        print(f"[STARTUP] WARN: Erreur DB au demarrage (mode degrade): {db_err}")
        print("[STARTUP] L'application demarre mais certaines fonctions peuvent etre indisponibles")

    # 2. Seed des systèmes SI (si la table est vide)
    try:
        from app.database import SessionLocal
        from app.models.systeme import Systeme
        from scripts.seed_systemes import seed_systemes
        db = SessionLocal()
        try:
            if db.query(Systeme).count() == 0:
                seed_systemes(db)
                print("[STARTUP] Systèmes SI seedés avec succès")
            else:
                print("[STARTUP] Systèmes SI déjà présents en base")
        finally:
            db.close()
    except Exception as e:
        print(f"[STARTUP] WARN: Erreur seed systèmes: {e}")

    # 3. Chargement du modele IA
    print("[STARTUP] Chargement du modele IA...")
    success = ai_service.load_models()
    if success:
        print("[STARTUP] Modele IA charge avec succes")
    else:
        print("[STARTUP] WARN: Modele IA non charge - mode fallback actif")

    # 4. V3.0 : Lancement de la tâche JIT (révocation automatique accès)
    print("[STARTUP] Lancement de la tâche JIT (révocation accès expirés)...")
    try:
        from app.tasks.jit_revoke_task import jit_revoke_loop
        asyncio.create_task(jit_revoke_loop())
        print("[STARTUP] Tâche JIT démarrée — Vérification toutes les 15 min")
    except Exception as jit_err:
        print(f"[STARTUP] WARN: Tâche JIT non lancée : {jit_err}")

    yield  # L'application tourne ici


app = FastAPI(
    title="Dashboard Intelligent iTop - Backend",
    description="Backend API pour la gestion intelligente des habilitations",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS standard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Inclusion des routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tickets_router)
app.include_router(ai_router)
app.include_router(notifications_router)
app.include_router(audit_router)
app.include_router(feedback_router)
app.include_router(employees_router)
app.include_router(systemes_router)   # ← Nouveau : /systemes
app.include_router(profiles_router)   # ← Nouveau : /profiles
app.include_router(portal_router)     # ← Modèle 2 : Portail Employé /portal
app.include_router(automation_rules_router)

# Créer le répertoire uploads si inexistant
os.makedirs("uploads/profiles", exist_ok=True)
# Monter le dossier static
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

# Middleware pour logger les requêtes (Audit interne & Debug)
@app.middleware("http")
async def log_requests(request, call_next):
    origin = request.headers.get('origin')
    print(f"\n[HTTP] {request.method} {request.url.path} (Origin: {origin})")
    try:
        response = await call_next(request)
        print(f"[HTTP] Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"[HTTP] ERREUR Interne: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur lors du traitement"},
            headers={"Access-Control-Allow-Origin": origin or "*"}
        )

@app.get("/")
def root():
    return {"message": "Backend prêt !", "status": "online", "cors": "activé"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}