# app/services/nlp_service.py
"""
Service NLP Léger — Analyse Sémantique des Justifications de Tickets (V3.0)
===========================================================================
Analyse la justification textuelle d'une demande d'accès pour détecter :
  - Justification LEGIT    → texte clair, contexte précis, urgence justifiée
  - Justification VAGUE    → mots génériques, pas de contexte métier
  - Justification SUSPICIEUSE → incohérences, rôle/urgence contradictoires
  - URGENT_SANS_MOTIF     → mot "urgent" sans contexte de justification

Approche : TF-IDF léger + patterns de mots-clés bancaires + scoring.
(Pas besoin de BERT/transformers — défendable scientifiquement en PFE)
"""

import re
import math
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Dictionnaires sémantiques bancaires
# ─────────────────────────────────────────────────────────────────────────────

# Mots légitimant une demande (réduisent le score de suspicion)
LEGIT_KEYWORDS = {
    "audit", "reglementaire", "bct", "conformite", "incident",
    "production", "bloquant", "deploiement", "version", "maintenance",
    "cloture", "comptable", "fin de mois", "autorisation", "manager",
    "approuve", "validé", "validation", "projet", "sprint", "release",
    "correction", "patch", "hotfix", "migration", "test", "qualification",
    "procedure", "protocole", "ticket", "demande formelle",
}

# Mots suspects (augmentent le score)
SUSPICIOUS_KEYWORDS = {
    "urgent", "rapidement", "vite", "maintenant", "immédiatement",
    "temporaire", "juste pour voir", "juste pour regarder", "exception",
    "juste cette fois", "besoin urgent", "pas le temps", "direct",
    "pas de raison", "personnel", "confidentiel", "secret",
    "pas pour longtemps", "quelques minutes", "accès rapide",
}

# Mots vagues — ne disent rien (score neutre mais signal de faible qualité)
VAGUE_KEYWORDS = {
    "besoin", "accès", "voir", "regarder", "travailler",
    "faire mon travail", "tâche", "mission", "nécessaire",
    "requis", "utile", "important", "indispensable", "obligatoire",
}

# Patterns de contexte métier précis (très legit)
BUSINESS_CONTEXT_PATTERNS = [
    r"incident\s+(production|prod|prd)\s+n[°o]?\s*[\w-]+",  # Incident prod avec référence
    r"cloture\s+comptable\s+\w+\s+\d{4}",                   # Clôture comptable avec date
    r"audit\s+(bct|reglementaire|interne)",                  # Audit officiel
    r"deploiement\s+(version|release|v\d)",                  # Déploiement avec version
    r"ticket\s+(iTop|jira|ref|n°|#)\s*[\w-]+",              # Référence ticket externe
]

MIN_LEGIT_LENGTH = 30    # En dessous : justification trop courte
MAX_SUSPICIOUS_RATIO = 0.3  # Plus de 30% de mots suspects → alerte


# ─────────────────────────────────────────────────────────────────────────────
# Service NLP
# ─────────────────────────────────────────────────────────────────────────────

class NLPService:

    def analyze_justification(
        self,
        justification: str,
        request_reason: str = "",
        role: str = "",
        environment: str = "",
    ) -> dict:
        """
        Analyse sémantique d'une justification de ticket.

        Retourne :
          {
            "nlp_score": int,           # 0 (très suspect) → 100 (très légitime)
            "nlp_label": str,           # LEGIT / VAGUE / SUSPICIOUS / URGENT_SANS_MOTIF
            "nlp_detail": str,          # Explication lisible
            "suspicious_words": list,   # Mots suspects trouvés
            "legit_words": list,        # Mots légitimants trouvés
            "has_business_context": bool,# True si pattern métier précis trouvé
            "justification_length": int, # Longueur texte
          }
        """
        text = (justification or "").lower().strip()
        reason = (request_reason or "").lower()

        # ── 0. Cas vide ──────────────────────────────────────────────────────
        if not text or len(text) < 5:
            return self._build_result(
                score=10,
                label="VAGUE",
                detail="Aucune justification fournie — demande non documentée.",
                suspicious=[],
                legit=[],
                has_ctx=False,
                length=0,
            )

        # ── 1. Tokenisation simple ────────────────────────────────────────────
        words = set(re.findall(r'\b[a-zàâäéèêëîïôùûüœæç]+\b', text))
        words_list = re.findall(r'\b[a-zàâäéèêëîïôùûüœæç]+\b', text)
        total_words = max(len(words_list), 1)

        # ── 2. Détection des mots-clés ────────────────────────────────────────
        found_legit      = [w for w in LEGIT_KEYWORDS if w in text]
        found_suspicious = [w for w in SUSPICIOUS_KEYWORDS if w in text]
        found_vague      = [w for w in VAGUE_KEYWORDS if w in text]

        # ── 3. Patterns de contexte métier ────────────────────────────────────
        has_business_context = any(
            re.search(p, text, re.IGNORECASE) for p in BUSINESS_CONTEXT_PATTERNS
        )

        # ── 4. Calcul du score de base ────────────────────────────────────────
        score = 50  # neutre

        # Bonus légitimité
        score += len(found_legit) * 8
        if has_business_context:
            score += 20
        if len(text) >= MIN_LEGIT_LENGTH:
            score += 10
        if len(text) >= 100:
            score += 5

        # Malus suspicion
        score -= len(found_suspicious) * 12
        suspicious_ratio = len(found_suspicious) / total_words
        if suspicious_ratio > MAX_SUSPICIOUS_RATIO:
            score -= 15

        # ── 5. Cohérence rôle / urgence ───────────────────────────────────────
        if environment in ("PRD", "PROD") and "urgent" in text and not found_legit:
            score -= 20  # Urgence en prod sans context = suspect

        # ── 6. Bonus reason alignée ───────────────────────────────────────────
        if reason == "audit_reglementaire_bct":
            score += 15
        elif reason == "incident_production_bloquant":
            score += 10
        elif reason == "demande_metier_urgente" and not found_legit:
            score -= 10

        # ── 7. Normalisation 0-100 ─────────────────────────────────────────────
        score = max(0, min(100, score))

        # ── 8. Label et détail ─────────────────────────────────────────────────
        if "urgent" in text and len(found_legit) == 0 and not has_business_context:
            label = "URGENT_SANS_MOTIF"
            detail = (
                "Urgence déclarée sans contexte métier identifiable. "
                "Aucune référence à un incident formalisé ou une procédure officielle."
            )
        elif score >= 65:
            label = "LEGIT"
            detail = (
                f"Justification documentée et cohérente. "
                f"{len(found_legit)} indicateur(s) de légitimité détecté(s)."
                + (" Contexte métier précis identifié." if has_business_context else "")
            )
        elif score >= 40:
            label = "VAGUE"
            detail = (
                "Justification présente mais insuffisamment précise. "
                "Aucun contexte métier vérifiable ou référence documentaire."
            )
        else:
            label = "SUSPICIOUS"
            detail = (
                f"Justification suspecte : {len(found_suspicious)} indicateur(s) "
                f"d'urgence non justifiée ou incohérence détectée."
            )

        return self._build_result(
            score=score,
            label=label,
            detail=detail,
            suspicious=found_suspicious[:5],
            legit=found_legit[:5],
            has_ctx=has_business_context,
            length=len(text),
        )

    def _build_result(
        self, score: int, label: str, detail: str,
        suspicious: list, legit: list, has_ctx: bool, length: int
    ) -> dict:
        return {
            "nlp_score":            score,
            "nlp_label":            label,
            "nlp_detail":           detail,
            "suspicious_words":     suspicious,
            "legit_words":          legit,
            "has_business_context": has_ctx,
            "justification_length": length,
        }

    def score_to_risk_modifier(self, nlp_score: int) -> int:
        """
        Convertit le score NLP en modificateur de score de risque.
        Utilisé par ai_service pour enrichir le calcul d'exposition.
        """
        if nlp_score < 20:
            return +25   # Très suspect → aggrave le risque
        elif nlp_score < 40:
            return +12
        elif nlp_score < 55:
            return +5
        elif nlp_score < 70:
            return 0     # Neutre
        elif nlp_score < 85:
            return -5
        else:
            return -10   # Très légitime → réduit le risque


# Singleton
nlp_service = NLPService()