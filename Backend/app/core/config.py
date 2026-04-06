# app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
import os
from dotenv import load_dotenv

# Chemin vers le .env dans app/
env_path = Path(__file__).parent.parent / ".env"
print(f"🔍 Chargement du .env depuis: {env_path}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ Fichier .env trouvé et chargé")
    
    # Afficher les variables chargées (sans le mot de passe)
    print(f"📧 SMTP_USERNAME: {os.getenv('SMTP_USERNAME')}")
    print(f"📧 EMAIL_FROM: {os.getenv('EMAIL_FROM')}")
    print(f"🌍 ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    print(f"🔌 ITOP_API_URL: {os.getenv('ITOP_API_URL') or 'Non configuré (mode simulation)'}")
else:
    print(f"❌ Fichier .env non trouvé à {env_path}")
    print("   Créez le fichier .env dans le dossier app/")

class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/itop_dashboard"
    
    # Sécurité
    SECRET_KEY: str = "super_secret_key_pfe_2026_change_moi_avec_une_longue_phrase"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@biat-it.com.tn")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Configuration iTop
    ITOP_API_URL: str = os.getenv("ITOP_API_URL", "")
    ITOP_USERNAME: str = os.getenv("ITOP_USERNAME", "")
    ITOP_PASSWORD: str = os.getenv("ITOP_PASSWORD", "")
    
    # CORS (ajouté pour centraliser)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

settings = Settings()

# Vérification finale
print("\n" + "="*50)
print("🔧 CONFIGURATION FINALE:")
print(f"📧 SMTP_USERNAME: {settings.SMTP_USERNAME or 'Non configuré'}")
print(f"📧 EMAIL_FROM: {settings.EMAIL_FROM}")
print(f"🌍 ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"🔌 Mode iTop: {'Réel' if settings.ITOP_API_URL else 'Simulation'}")
print("="*50 + "\n")