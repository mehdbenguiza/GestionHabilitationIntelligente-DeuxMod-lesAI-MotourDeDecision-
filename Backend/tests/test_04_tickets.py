# tests/test_04_tickets.py
"""
TEST 6 & 7 — Gestion des tickets
  - GET  /tickets              → liste vide (DB propre) ou items valides
  - GET  /tickets/{id}         → 404 si inexistant
  - POST /tickets/simulate/create → crée un ticket avec classification IA
"""

import pytest


def test_get_tickets_authenticated(client, auth_headers):
    """Un utilisateur connecté peut lister les tickets (résultat = liste)."""
    response = client.get("/tickets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_ticket_not_found(client, auth_headers):
    """Un ticket inexistant retourne 404."""
    response = client.get("/tickets/999999", headers=auth_headers)
    assert response.status_code == 404


def test_get_tickets_unauthenticated(client):
    """Sans token, la liste de tickets est refusée (401)."""
    response = client.get("/tickets")
    assert response.status_code == 401


def test_simulate_create_ticket(client, auth_headers):
    """
    POST /tickets/simulate/create crée un ticket simulé
    avec une classification IA.
    """
    response = client.post("/tickets/simulate/create", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Structure minimale attendue
    assert "ticket" in data
    ticket = data["ticket"]
    assert "id" in ticket
    assert "ref" in ticket
    assert ticket["ref"].startswith("SIM-")

    # La classification IA doit être présente
    assert "ai_classification" in ticket
    ai = ticket["ai_classification"]
    assert "level" in ai
    # Le modèle peut retourner CRITIQUE (FR) ou CRITICAL (EN)
    assert ai["level"] in ["BASE", "SENSITIVE", "CRITIQUE", "CRITICAL"]
    assert "confidence" in ai
    # La confidence est en pourcentage (0-100)
    assert 0.0 <= float(ai["confidence"]) <= 100.0
