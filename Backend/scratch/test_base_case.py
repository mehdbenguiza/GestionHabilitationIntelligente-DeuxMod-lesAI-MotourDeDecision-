# scratch/test_base_case.py
import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.services.ai_service import ai_service

# Cas très simple et sûr : 
# Senior, Team MOE (Dev), App E_BANKING, Env DEV2, Access READ, Ressource non sensible.
safe_ticket = {
    "team": "MOE",
    "role": "DEVELOPPEUR",
    "application": "E_BANKING",
    "environment": "DEV2",
    "access_type": "READ",
    "resource": "OTHER",
    "user_seniority": "senior",
    "request_reason": "maintenance_preventive",
    "manager_approval_status": "approved"
}

# Initialiser le service (chargement modèles)
ai_service.load_models()

print("\n--- Test Classification CASE SAFE ---")
result = ai_service.classify_ticket_data(safe_ticket)
print(f"Niveau Prédit : {result['level']}")
print(f"Confiance : {result['confidence']}%")
print(f"Score Risque Règles : {result['risk_score_rules']}")
if 'consistency' in result:
    print(f"Cohérence : {result['consistency']['status']} ({result['consistency']['message']})")
print(f"Règles déclenchées : {result['triggered_rules']}")
