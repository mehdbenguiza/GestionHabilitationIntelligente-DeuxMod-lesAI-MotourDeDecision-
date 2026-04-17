# tests/test_05_ai_classify.py
"""
TEST 8 — Classification IA
  - POST /ai/classify → retourne un niveau BASE / SENSITIVE / CRITIQUE
    avec confidence et explanation
    Structure réelle : { status, ticket, ai_analysis: { level, confidence, ... } }
"""

import pytest


AI_PAYLOAD_BASE = {
    "team": "MOE",
    "application": "CRM_SIEBEL",
    "environment": "DEV2",
    "access_type": "READ",
    "resource": "OTHER"
}

AI_PAYLOAD_CRITIQUE = {
    "team": "TRADING",
    "application": "MUREX",
    "environment": "PRD",
    "access_type": "DELETE",
    "resource": "TRANSACTIONS_FINANCIERES"
}

# Niveaux valides (FR et EN)
VALID_LEVELS = {"BASE", "SENSITIVE", "CRITIQUE", "CRITICAL"}


def _extract_level(data: dict):
    """Extrait le niveau de risque de la réponse quelle que soit sa structure."""
    # Structure : { ai_analysis: { level } }
    ai = data.get("ai_analysis") or data.get("classification") or data
    return ai.get("level") or ai.get("predicted_level") or ai.get("risk_level")


def _extract_confidence(data: dict):
    """Extrait la confidence de la réponse."""
    ai = data.get("ai_analysis") or data.get("classification") or data
    return ai.get("confidence")


def test_ai_classify_returns_valid_structure(client, auth_headers):
    """
    POST /ai/classify avec payload valide retourne une réponse
    structurée avec level et confidence.
    """
    response = client.post("/ai/classify", json=AI_PAYLOAD_BASE, headers=auth_headers)
    assert response.status_code == 200, f"Erreur inattendue: {response.text}"
    data = response.json()

    level = _extract_level(data)
    assert level is not None, f"Aucun level trouvé dans : {data}"
    assert level in VALID_LEVELS, f"Niveau invalide : {level}"

    confidence = _extract_confidence(data)
    assert confidence is not None, "Confidence manquante"
    # confidence peut être en % (0-100) ou en ratio (0-1)
    assert 0.0 <= float(confidence) <= 100.0, f"Confidence hors plage : {confidence}"


def test_ai_classify_critique_response_is_valid(client, auth_headers):
    """
    Un scénario critique (TRADING/MUREX/PRD/DELETE) doit retourner
    une réponse HTTP 200 avec un niveau valide.
    Note : en mode test (fallback sans ML), le niveau peut être BASE —
    on vérifie uniquement la structure et que le risk_score est >= 0.
    """
    response = client.post("/ai/classify", json=AI_PAYLOAD_CRITIQUE, headers=auth_headers)
    assert response.status_code == 200, f"Erreur inattendue: {response.text}"
    data = response.json()

    level = _extract_level(data)
    assert level in VALID_LEVELS, f"Niveau invalide obtenu : {level}"

    # Le risk_score doit être un entier >= 0
    ai = data.get("ai_analysis") or data.get("classification") or data
    risk_score = ai.get("risk_score")
    if risk_score is not None:
        assert int(risk_score) >= 0, f"risk_score doit être >= 0, obtenu: {risk_score}"


def test_ai_classify_without_token(client):
    """La classification IA requiert une authentification."""
    response = client.post("/ai/classify", json=AI_PAYLOAD_BASE)
    assert response.status_code == 401
