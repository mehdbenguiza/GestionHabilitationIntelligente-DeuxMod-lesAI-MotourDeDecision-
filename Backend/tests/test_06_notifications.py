# tests/test_06_notifications.py
"""
TEST 9 — Notifications
  - GET  /notifications       → liste (éventuellement vide)
  - PATCH /notifications/{id}/read → marquer comme lue
"""

import pytest


def test_get_notifications_authenticated(client, auth_headers):
    """Un utilisateur connecté peut récupérer ses notifications."""
    response = client.get("/notifications", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Doit être une liste (possiblement vide)
    assert isinstance(data, list)


def test_get_notifications_unauthenticated(client):
    """Sans token, les notifications sont inaccessibles."""
    response = client.get("/notifications")
    assert response.status_code == 401


def test_get_current_user_info(client, auth_headers):
    """GET /users/me retourne les infos de l'utilisateur connecté."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # La réponse contient au moins le rôle et l'email
    assert "role" in data
    assert data["role"] == "SUPER_ADMIN"
    assert "email" in data
    assert data["email"] == "superadmin@test.biat"
