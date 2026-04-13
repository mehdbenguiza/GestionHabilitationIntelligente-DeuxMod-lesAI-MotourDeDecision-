# scratch/test_ai_logic.py

import sys
import os

# Ajouter le chemin du projet
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.services.ai_service import ai_service

def test():
    # 1. Charger les modèles
    ai_service.load_models()
    
    # 2. Scénario 1: Junior en PRD avec DELETE (Doit être CRITICAL + Haut Score)
    ticket_data_crutical = {
        "team": "MOE",
        "role": "STAGIAIRE",
        "application": "T24",
        "environment": "PRD",
        "access_type": "DELETE",
        "resource": "TRANSACTIONS_FINANCIERES",
        "user_seniority": "junior",
        "request_reason": "demande_metier_urgente",
        "manager_approval_status": "none"
    }
    
    print("\n" + "="*50)
    print("TEST SCÉNARIO CRITIQUE")
    print("="*50)
    result = ai_service.classify_ticket_data(ticket_data_crutical)
    print(f"Level: {result['level']} ({result['risk_label']})")
    print(f"Score: {result['risk_score']}")
    print(f"Confidence: {result['confidence']}%")
    print("Explanation:")
    print(result['explanation'])

    # 3. Scénario 2: Senior en DEV (Doit être BASE)
    ticket_data_base = {
        "team": "MOE",
        "role": "DEVELOPPEUR",
        "application": "CRM_SIEBEL",
        "environment": "DEV2",
        "access_type": "READ",
        "resource": "OTHER",
        "user_seniority": "senior",
        "request_reason": "maintenance_preventive",
        "manager_approval_status": "approved"
    }
    
    print("\n" + "="*50)
    print("TEST SCÉNARIO BASE")
    print("="*50)
    result = ai_service.classify_ticket_data(ticket_data_base)
    print(f"Level: {result['level']} ({result['risk_label']})")
    print(f"Score: {result['risk_score']}")
    print(f"Confidence: {result['confidence']}%")
    print("Explanation:")
    print(result['explanation'])

if __name__ == "__main__":
    test()
