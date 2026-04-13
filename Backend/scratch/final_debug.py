# scratch/final_debug.py
import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.database import SessionLocal, engine
from app.models.ticket import Ticket
from app.models.classification_result import ClassificationResult
from app.services.ticket_service import TicketService
from app.api.endpoints.tickets import serialize_ticket

db = SessionLocal()

print("--- Step 1: Searching for tickets ---")
try:
    tickets = db.query(Ticket).limit(5).all()
    print(f"Found {len(tickets)} tickets.")
    for t in tickets:
        print(f"Ticket ID: {t.id}, Ref: {t.ref}")
        try:
            # Let's see if accessing the relationship fails
            print(f"  Classification: {t.classification}")
        except Exception as e:
            print(f"  ❌ Error accessing relationship: {e}")
            import traceback
            traceback.print_exc()
            
        try:
            # Let's see if serialization fails
            s = serialize_ticket(t)
            print(f"  ✅ Serialized successfully")
        except Exception as e:
            print(f"  ❌ Error serializing: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"❌ Error querying tickets: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Step 2: Testing /ai/metrics logic ---")
try:
    from app.models.decision_engine import DecisionEngine
    from sqlalchemy import func
    total = db.query(ClassificationResult).count()
    print(f"Total classifications: {total}")
    
    levels = db.query(ClassificationResult.predicted_level, func.count(ClassificationResult.id)).group_by(ClassificationResult.predicted_level).all()
    print(f"Levels: {levels}")
    
except Exception as e:
    print(f"❌ Error in metrics logic: {e}")
    import traceback
    traceback.print_exc()

db.close()
