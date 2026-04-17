# tests/test_01_health.py
"""
TEST 1 & 2 — Santé de l'API
  - GET /       → le backend répond
  - GET /health → retourne un timestamp valide
"""

import pytest


def test_root_is_online(client):
    """L'API répond 200 sur la route racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_health_check_returns_ok(client):
    """GET /health retourne status='ok' avec un timestamp ISO."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    # Le timestamp doit être une chaîne ISO 8601 non vide
    assert isinstance(data["timestamp"], str) and len(data["timestamp"]) > 0
