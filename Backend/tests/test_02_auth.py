# tests/test_02_auth.py
"""
TEST 3 & 4 — Authentification
  - POST /auth/login avec identifiants corrects → 200 + token
  - POST /auth/login avec mauvais mot de passe  → 400
"""

import pytest


def test_login_success(client, super_admin):
    """Connexion valide retourne un access_token."""
    response = client.post("/auth/login", json={
        "username": "test_superadmin",
        "password": "Admin1234!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, super_admin):
    """Connexion avec mauvais mot de passe retourne 400."""
    response = client.post("/auth/login", json={
        "username": "test_superadmin",
        "password": "MauvaisMotDePasse!"
    })
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_login_unknown_user(client):
    """Connexion avec utilisateur inexistant retourne 400."""
    response = client.post("/auth/login", json={
        "username": "utilisateur_fantome",
        "password": "N'importeQuoi123!"
    })
    assert response.status_code == 400
