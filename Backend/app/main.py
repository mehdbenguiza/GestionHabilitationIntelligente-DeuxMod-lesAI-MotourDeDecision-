from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.tickets import router as tickets_router
from app.api.endpoints.feedback import router as feedback_router
from app.api.endpoints.employees import router as employees_router
from app.database import engine, Base
from datetime import datetime
from app.api.endpoints.ai import router as ai_router
from app.api.endpoints.notifications import router as notifications_router
from app.api.endpoints.audit import router as audit_router
from app.services.ai_service import ai_service
# Imports des modèles pour forcer la création des tables
import app.models.notification
import app.models.classification_result
import app.models.decision_engine
import app.models.audit_log
import app.models.employee
import app.models.ai_feedback   # ← Nouveau : feedback + corrections

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dashboard Intelligent iTop - Backend",
    description="Backend API pour la gestion intelligente des habilitations",
    version="1.0.0",
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
        print(f"[HTTP] ❌ ERREUR Interne: {e}")
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
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
@app.on_event("startup")
async def startup_event():
    print("🚀 Démarrage de l'application...")
    success = ai_service.load_models()
    if success:
        print("✅ IA chargée avec succès")
    else:
        print("❌ Échec du chargement de l'IA")