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
    # MySQL / PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,   # Vérifie que la connexion est toujours active
        pool_recycle=3600,    # Recycle les connexions chaque heure
        echo=False            # Mettre True pour debug SQL
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()