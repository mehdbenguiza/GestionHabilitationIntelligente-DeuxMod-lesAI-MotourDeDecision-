# scratch/debug_ticket_404.py
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import DashboardUser, Role
from app.core.security import get_password_hash

# Config DB de test
engine = create_engine("sqlite:///./debug.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Créer un user pour le token
db = TestingSessionLocal()
if not db.query(DashboardUser).filter_by(username="debug").first():
    user = DashboardUser(
        username="debug",
        fullName="Debug User",
        email="debug@test.tn",
        passwordHash=get_password_hash("Debug123!"),
        role=Role.SUPER_ADMIN,
        isActive=True
    )
    db.add(user)
    db.commit()

# Login
login_resp = client.post("/auth/login", json={"username": "debug", "password": "Debug123!"})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n🔍 Test GET /tickets/999999 (Inexistant)")
resp = client.get("/tickets/999999", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.json()}")

if resp.status_code == 500:
    print("\n❗ L'erreur 500 est confirmée. Vérification de la cause possible...")
