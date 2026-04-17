# scratch/test_notification_and_history.py
import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, Base, engine
from app.models.ticket import Ticket, TicketStatus
from app.models.classification_result import ClassificationResult
from app.models.notification import Notification
from app.services.ai_service import AIService

def test_critical_notification():
    # S'assurer que les tables existent (avec les nouveaux index/relations)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    ai_service = AIService()

    print("\n--- TEST: TICKET CRITIQUE ET NOTIFICATION ---")
    
    # 1. Créer un ticket qui sera classé critique par les règles
    # Un junior sur PRD avec DELETE access est 100% critique
    test_ticket = Ticket(
        ref=f"TEST-CRIT-{datetime.now().strftime('%M%S')}",
        employee_id="EMP001",
        employee_name="Test User",
        employee_email="test@example.com",
        team_name="DEV",
        role="DEVELOPPEUR",
        description="Test critical notification",
        requested_environments=["PRD"],
        requested_access_details={
            "access_types": ["DELETE"],
            "application": "T24",
            "resource": "DONNEES_CLIENTS_SENSIBLES",
            "user_seniority": "junior"
        }
    )
    db.add(test_ticket)
    db.commit()
    db.refresh(test_ticket)
    
    print(f"Ticket cree: {test_ticket.ref} (ID: {test_ticket.id})")

    # 2. Lancer la classification
    print("Classification en cours...")
    ai_service.classify_and_save(db, test_ticket)
    db.commit()
    db.refresh(test_ticket)

    # 3. Vérifier les résultats
    print(f"Niveau IA: {test_ticket.ai_level}")
    
    # Historique
    count = db.query(ClassificationResult).filter(ClassificationResult.ticket_id == test_ticket.id).count()
    print(f"Nombre d'analyses en historique: {count}")

    # Notifications
    last_notif = db.query(Notification).order_by(Notification.created_at.desc()).first()
    if last_notif and "ALERTE: Ticket Critique" in last_notif.title:
        print(f"✅ Notification OK: {last_notif.title}")
    else:
        print("❌ Echec: Notification non trouvee ou incorrecte")

    # Property test
    if test_ticket.classification:
        print(f"✅ Property classification OK: {test_ticket.classification.predicted_level}")

    db.close()

if __name__ == "__main__":
    test_critical_notification()
