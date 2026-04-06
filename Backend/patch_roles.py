import sys
import os
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app.models.ticket import Ticket

ROLES_PER_TEAM = {
    "MOE": ["DEVELOPPEUR", "TECH_LEAD", "CHEF_DE_PROJET", "STAGIAIRE"],
    "MOA": ["BUSINESS_ANALYST", "PRODUCT_OWNER", "CHEF_DE_PROJET"],
    "RESEAU": ["INGENIEUR_RESEAU", "ADMINISTRATEUR", "STAGIAIRE"],
    "SECURITE": ["ANALYSTE_SOC", "RSSI", "PENTESTER"],
    "TEST_FACTORY": ["TESTEUR_QA", "TEST_LEAD", "AUTOMATICIEN"],
    "DATA": ["DATA_SCIENTIST", "DATA_ENGINEER", "DATA_ANALYST"],
    "MXP": ["INTEGRATEUR", "CHEF_DE_PROJET", "DEVELOPPEUR_MXP"]
}

db = SessionLocal()
tickets = db.query(Ticket).filter((Ticket.role == None) | (Ticket.role == "") | (Ticket.role == "None")).all()
for t in tickets:
    team = t.team_name if t.team_name in ROLES_PER_TEAM else "MOE"
    role = random.choice(ROLES_PER_TEAM.get(team, ["DEVELOPPEUR"]))
    t.role = role
db.commit()
db.close()
print(f"✅ Patched {len(tickets)} tickets missing roles.")
