# scripts/setup_users.py
import os
import sys
from datetime import datetime

# Ajouter le chemin du projet pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.user import DashboardUser, Role
from app.core.security import get_password_hash

def setup_users():
    print("=" * 60)
    print("[STARTUP] Creation des comptes Administrateur & Super Admin")
    print("=" * 60)

    # Créer les tables au cas où
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    users_to_create = [
        {
            "username": "benguiza",
            "fullName": "Mehdi Ben Guiza (Super Admin)",
            "email": "benguizamehdi3@gmail.com",
            "password": "Mehdiforyou123!",
            "role": Role.SUPER_ADMIN
        },
        {
            "username": "bengui1",
            "fullName": "Bengui Admin",
            "email": "benguizamehdi2@gmail.com",
            "password": "Mehdiforyou123!",
            "role": Role.ADMIN
        }
    ]

    try:
        for u in users_to_create:
            # Vérifier si l'utilisateur existe déjà
            existing = db.query(DashboardUser).filter(
                (DashboardUser.username == u["username"]) | 
                (DashboardUser.email == u["email"])
            ).first()
            
            if existing:
                print(f"[SKIP] L'utilisateur '{u['username']}' ({u['email']}) existe deja. Mise a jour du role et du mot de passe...")
                existing.passwordHash = get_password_hash(u["password"])
                existing.role = u["role"]
                existing.isActive = True
                continue

            new_user = DashboardUser(
                username=u["username"],
                fullName=u["fullName"],
                email=u["email"],
                passwordHash=get_password_hash(u["password"]),
                role=u["role"],
                isActive=True,
                createdAt=datetime.utcnow()
            )
            db.add(new_user)
            print(f"[OK] Utilisateur '{u['username']}' cree avec succes ({u['role'].value})")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Erreur lors de la creation : {e}")
    finally:
        db.close()

    print("\n[DONE] Configuration des utilisateurs terminee !")

if __name__ == "__main__":
    setup_users()
