from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ✅ CORRECTION BUG 3 : Gérer SQLite et MySQL différemment
# SQLite nécessite check_same_thread=False pour fonctionner avec FastAPI (multi-thread)
DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Mettre True pour debug SQL
    )
else:
    # MySQL / PostgreSQL — config robuste pour XAMPP et production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,       # Vérifie la connexion avant chaque requête (évite WinError 10054)
        pool_recycle=1800,        # Recycle les connexions toutes les 30 min (au lieu de 1h)
        pool_size=5,              # Nombre de connexions persistantes dans le pool
        max_overflow=10,          # Connexions supplémentaires autorisées en pic
        pool_timeout=30,          # Attendre max 30s pour une connexion disponible
        connect_args={
            "connect_timeout": 60,        # Timeout de connexion initiale
            "read_timeout":    60,        # Timeout de lecture MySQL
            "write_timeout":   60,        # Timeout d'écriture MySQL
        },
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()