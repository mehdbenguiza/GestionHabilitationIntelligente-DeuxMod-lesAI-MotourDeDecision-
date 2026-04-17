# tests/test_03_create_user.py
"""
TEST 5 — Création d'un utilisateur (admin)
  - POST /auth/register  (réservé Super Admin)
    → 200 : l'utilisateur est créé
    → 400 : username déjà pris
    → 401/403 : sans token
"""

import pytest


def test_create_user_as_super_admin(client, auth_headers):
    """Un super-admin peut créer un nouvel admin."""
    payload = {
        "username": "new_admin_test",
        "fullName": "Nouvel Admin Test",
        "email": "new_admin@biat-test.tn",
        "password": "Admin1234!",
        "role": "ADMIN"
    }
    response = client.post("/auth/register", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "new_admin_test" in data.get("msg", "")


def test_create_user_duplicate_username(client, auth_headers):
    """Créer deux fois le même username retourne 400."""
    payload = {
        "username": "dup_admin_test",
        "fullName": "Doublon Admin",
        "email": "dup1@biat-test.tn",
        "password": "Admin1234!",
        "role": "ADMIN"
    }
    # Première création : doit réussir
    r1 = client.post("/auth/register", json=payload, headers=auth_headers)
    assert r1.status_code == 200

    # Deuxième fois : username déjà pris → 400
    payload["email"] = "dup2@biat-test.tn"   # email différent mais même username
    r2 = client.post("/auth/register", json=payload, headers=auth_headers)
    assert r2.status_code == 400
    assert "déjà pris" in r2.json().get("detail", "").lower() or "already" in r2.json().get("detail", "").lower()


def test_create_user_without_token(client):
    """Sans token, l'enregistrement est refusé (401)."""
    payload = {
        "username": "anon_user",
        "fullName": "Anon",
        "email": "anon@biat-test.tn",
        "password": "Admin1234!",
        "role": "ADMIN"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 401
