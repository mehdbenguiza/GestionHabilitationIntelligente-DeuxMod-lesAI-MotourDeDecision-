# scripts/create_test_tickets.py

import requests
import json

API_URL = "http://127.0.0.1:8000"

def login():
    """Se connecter pour obtenir le token"""
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"username": "superadmin", "password": "superadmin"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("❌ Échec de connexion")
        return None

def create_ticket(token, ticket_data):
    """Créer un ticket via l'API (simulation)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/tickets/simulate/create",
        headers=headers,
        json=ticket_data
    )
    return response

def create_multiple_tickets(token, count=5):
    """Créer plusieurs tickets de test"""
    for i in range(count):
        # Tu peux varier les données ici
        ticket_data = {
            "title": f"Ticket de test {i+1}",
            "description": "Demande d'accès pour test",
            "environments": ["T24_DEV2"],
            "access_rights": ["LECTURE", "ECRITURE"]
        }
        response = create_ticket(token, ticket_data)
        if response.status_code == 200:
            print(f"✅ Ticket {i+1} créé")
        else:
            print(f"❌ Erreur ticket {i+1}: {response.text}")

if __name__ == "__main__":
    token = login()
    if token:
        create_multiple_tickets(token, 10)
    else:
        print("Impossible de créer les tickets")