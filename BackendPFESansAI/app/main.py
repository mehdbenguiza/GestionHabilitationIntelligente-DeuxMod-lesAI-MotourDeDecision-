from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.users import router as users_router
from app.api.endpoints.tickets import router as tickets_router   # ← NOUVEAU
from app.database import engine, Base
from datetime import datetime

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dashboard Intelligent iTop - Backend")

# Middleware CORS personnalisé
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Ajouter les headers CORS à TOUTES les réponses
        origin = request.headers.get('origin')
        if origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin"
        
        return response

# Ajouter le middleware personnalisé
app.add_middleware(CustomCORSMiddleware)

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
app.include_router(tickets_router)   # ← NOUVEAU

# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"\n🔵 Requête reçue: {request.method} {request.url.path}")
    print(f"📋 Origin: {request.headers.get('origin')}")
    
    response = await call_next(request)
    
    print(f"🟢 Réponse: {response.status_code}")
    print(f"📋 Response Headers CORS: {response.headers.get('access-control-allow-origin')}")
    
    return response

@app.get("/")
def root():
    return {"message": "Backend prêt !", "status": "online", "cors": "activé"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}