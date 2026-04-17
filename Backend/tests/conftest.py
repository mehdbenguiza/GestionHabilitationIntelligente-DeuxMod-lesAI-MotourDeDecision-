# tests/conftest.py
"""
Fixtures partagées entre tous les modules de tests.
On utilise une base SQLite en mémoire isolée pour chaque session de test.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import DashboardUser, Role
from app.core.security import get_password_hash

# ── Base SQLite en mémoire (isolée, détruite après les tests) ────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_unit.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Crée toutes les tables une seule fois pour la session de tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Session DB de test — rollback après chaque test pour isolation."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """Client HTTP FastAPI avec override de la dépendance get_db."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def super_admin(db):
    """Crée un super-admin en base et le retourne."""
    existing = db.query(DashboardUser).filter_by(username="test_superadmin").first()
    if existing:
        return existing
    user = DashboardUser(
        username="test_superadmin",
        fullName="Test SuperAdmin",
        email="superadmin@test.biat",
        passwordHash=get_password_hash("Admin1234!"),
        role=Role.SUPER_ADMIN,
        isActive=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def admin_token(client, super_admin):
    """Retourne un Bearer token valide pour le super-admin de test."""
    resp = client.post("/auth/login", json={
        "username": "test_superadmin",
        "password": "Admin1234!"
    })
    assert resp.status_code == 200, f"Login échoué: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token):
    """Headers HTTP avec Bearer token, utilisables dans chaque test."""
    return {"Authorization": f"Bearer {admin_token}"}
