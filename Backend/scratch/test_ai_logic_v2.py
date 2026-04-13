# scratch/test_ai_logic_v2.py

import sys
import os
import json

# Ajouter le chemin du projet
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from app.services.ai_service import ai_service

def test():
    # 1. Charger les modèles
    print("Chargement des modèles...")
    ai_service.load_models()
    
    # 2. Scénario 1: Junior en PRD avec DELETE (Doit être CRITICAL + Incohérence si ML dit BASE)
    ticket_data_critical = {
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
    
    print("\n" + "="*60)
    print("TEST SCÉNARIO CRITIQUE (v2.0 Hybride)")
    print("="*60)
    result = ai_service.classify_ticket_data(ticket_data_critical)
    
    print(f"Prediction ML: {result['prediction']}")
    print(f"Rule Level:    {result['rule_based_level']}")
    print(f"Risk Score:    {result['risk_score_rules']} pts")
    print(f"Confidence:    {result['confidence']}% ({result['confidence_level']})")
    print(f"Consistency:   {result['consistency']['status']} - {result['consistency']['message']}")
    print(f"Action Rec:    {result['recommended_action']}")
    print("\nRules Déclenchées:")
    for rule in result['triggered_rules']:
        print(f"  {rule}")
    
    print("\nExplanation (Aperçu):")
    print("-" * 20)
    print(result['explanation'][:200] + "...")
    print("-" * 20)

    # 3. Scénario 2: Junior + PRD (sans DELETE) -> Score 50 + 25 = 75 (SENSITIVE)
    ticket_data_sensitive = {
        "team": "MOE",
        "role": "DEVELOPPEUR",
        "application": "E_BANKING",
        "environment": "PRD",
        "access_type": "READ",
        "resource": "OTHER",
        "user_seniority": "junior",
        "request_reason": "maintenance_preventive",
        "manager_approval_status": "none"
    }

    print("\n" + "="*60)
    print("TEST SCÉNARIO SENSITIVE (v2.0 Hybride)")
    print("="*60)
    result = ai_service.classify_ticket_data(ticket_data_sensitive)
    print(f"Prediction ML: {result['prediction']}")
    print(f"Rule Level:    {result['rule_based_level']}")
    print(f"Risk Score:    {result['risk_score_rules']} pts")
    print(f"Consistency:   {result['consistency']['status']}")
    print(f"Action Rec:    {result['recommended_action']}")

    # 4. Scénario 3: Senior + DEV + Approved -> Score 15 (FULL_ACCESS dev) - 20 (Approval) = -5 (BASE)
    ticket_data_base = {
        "team": "MOE",
        "role": "DEVELOPPEUR",
        "application": "CRM_SIEBEL",
        "environment": "DEV2",
        "access_type": "FULL_ACCESS",
        "resource": "OTHER",
        "seniority": "senior",
        "request_reason": "maintenance_preventive",
        "manager_approval_status": "approved"
    }

    print("\n" + "="*60)
    print("TEST SCÉNARIO BASE (v2.0 Hybride)")
    print("="*60)
    result = ai_service.classify_ticket_data(ticket_data_base)
    print(f"Prediction ML: {result['prediction']}")
    print(f"Rule Level:    {result['rule_based_level']}")
    print(f"Risk Score:    {result['risk_score_rules']} pts")
    print(f"Action Rec:    {result['recommended_action']}")

if __name__ == "__main__":
    test()
