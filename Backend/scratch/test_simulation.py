import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.employee import Employee
from app.services.ticket_service import TicketService
from app.core.config import settings

db = SessionLocal()

# Stats employees
total   = db.query(Employee).count()
juniors = db.query(Employee).filter(Employee.seniority == "junior").count()
seniors = db.query(Employee).filter(Employee.seniority == "senior").count()
print(f"Employes en base : {total}")
print(f"  - Juniors : {juniors}")
print(f"  - Seniors : {seniors}")

# Test simulation
settings.ENVIRONMENT = "development"
svc = TicketService(db)
result = svc.simulate_create_ticket()
t = result["ticket"]
details = t.get("access", {})

print("")
print("Ticket simule OK:")
print("  Ref         :", t["ref"])
print("  Employe     :", t["employee_name"], "-", t["team"], "/", t["role"])
print("  Seniorite   :", details.get("user_seniority"))
print("  Application :", t["application"])
print("  Env         :", t["environments"])
print("  Acces       :", details.get("access_types"))
print("  IA Level    :", t["ai_classification"]["level"])
print("  Confidence  :", t["ai_classification"]["confidence"], "%")

db.close()
