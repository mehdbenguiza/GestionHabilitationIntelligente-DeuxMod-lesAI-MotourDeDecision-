# app/services/decision_fusion_service.py
"""
Decision Fusion Engine — Fusion Modèle 1 + Modèle 2
=====================================================
Combine la classification (Modèle 1 : RF/XGBoost + Règles Métier)
avec la détection d'anomalies comportementales (Modèle 2 : Isolation Forest + Règles).

Table de fusion :
┌─────────────┬──────────────────┬─────────────────┬────────────────────────────────────┐
│  Modèle 1   │  Modèle 2        │  Décision Finale│  Logique                           │
├─────────────┼──────────────────┼─────────────────┼────────────────────────────────────┤
│ BASE        │ NONE (normal)    │ BASE            │ Tout normal                        │
│ BASE        │ LOW              │ SENSITIVE       │ Anomalie légère → élève le niveau  │
│ BASE        │ MEDIUM           │ SENSITIVE       │ Anomalie modérée → élève           │
│ BASE        │ HIGH/CRITICAL    │ CRITICAL        │ Anomalie grave → CRITICAL direct   │
│ SENSITIVE   │ NONE             │ SENSITIVE       │ Modèle 1 prime                     │
│ SENSITIVE   │ LOW/MEDIUM       │ SENSITIVE       │ Confirmé + score aggravé           │
│ SENSITIVE   │ HIGH/CRITICAL    │ CRITICAL        │ Anomalie grave → CRITICAL          │
│ CRITICAL    │ N'importe        │ CRITICAL        │ Niveau max, immuable               │
└─────────────┴──────────────────┴─────────────────┴────────────────────────────────────┘

PRINCIPE CLÉ : La présence d'une anomalie ne peut qu'AUGMENTER le niveau, jamais le diminuer.
"""


# ─── Mapping sévérité anomalie → niveau de risque minimum imposé ─────────────
ANOMALY_MIN_LEVEL = {
    "NONE":     "BASE",
    "LOW":      "SENSITIVE",
    "MEDIUM":   "SENSITIVE",
    "HIGH":     "CRITICAL",
    "CRITICAL": "CRITICAL",
}

LEVEL_ORDER = {"BASE": 0, "SENSITIVE": 1, "CRITICAL": 2}


class DecisionFusionService:
    """
    Fusionne les résultats du Modèle 1 (classification) et du Modèle 2 (anomalie)
    pour produire une décision finale enrichie et cohérente.
    """

    def fuse(self, model1_result: dict, anomaly_result: dict) -> dict:
        """
        Fusionne les deux résultats et retourne la décision finale.

        Args:
            model1_result  : résultat de ai_service.classify_ticket_model()
            anomaly_result : résultat de anomaly_service.analyze_ticket()

        Returns:
            dict avec les clés :
              - final_level          : "BASE" | "SENSITIVE" | "CRITICAL"
              - original_level       : niveau initial du Modèle 1
              - anomaly_severity     : sévérité du Modèle 2
              - anomaly_flags        : liste des flags détectés
              - is_anomalous         : bool
              - anomaly_overridden   : bool (True si le Modèle 2 a élevé le niveau)
              - final_risk_score     : score de risque final (Modèle1 + boost anomalie)
              - anomaly_score        : score IF brut
              - fusion_explanation   : explication combine complte
              - risk_boost           : points ajoutés par l'anomalie
        """
        # ── Extraire les données du Modèle 1 ────────────────────────────────
        m1_level      = model1_result.get("level", "BASE")
        # IMPORTANT: Utiliser risk_score_rules (post NLP+Trust) et non risk_score (pré-modificateurs)
        # Cela garantit que final_risk_score = sum(risk_factors) = risk_score_rules affiché
        m1_risk_score = model1_result.get("risk_score_rules", model1_result.get("risk_score", 0))
        m1_explanation = model1_result.get("explanation", "")

        # ── Extraire les données du Modèle 2 ────────────────────────────────
        anomaly_severity = anomaly_result.get("severity", "NONE")
        anomaly_flags    = anomaly_result.get("flags", [])
        is_anomalous     = anomaly_result.get("is_anomalous", False)
        risk_boost       = anomaly_result.get("risk_boost", 0)
        anomaly_score_if = anomaly_result.get("anomaly_score")
        anomaly_expl     = anomaly_result.get("explanation", "")

        # ── Calcul du niveau final ───────────────────────────────────────────
        # Le niveau final est le MAX entre Modèle 1 et le minimum imposé par l'anomalie
        m2_min_level = ANOMALY_MIN_LEVEL.get(anomaly_severity, "BASE")

        m1_order  = LEVEL_ORDER.get(m1_level, 0)
        m2_order  = LEVEL_ORDER.get(m2_min_level, 0)

        if m1_order >= m2_order:
            final_level = m1_level
            anomaly_overridden = False
        else:
            final_level = m2_min_level
            anomaly_overridden = True

        # ── Score de risque final ────────────────────────────────────────────
        final_risk_score = min(200, m1_risk_score + risk_boost)

        # ── Explication fusionnée ────────────────────────────────────────────
        fusion_explanation = self._build_fusion_explanation(
            m1_level, m1_explanation,
            final_level, anomaly_severity, anomaly_flags,
            anomaly_expl, anomaly_overridden, risk_boost
        )

        return {
            "final_level":         final_level,
            "original_level":      m1_level,
            "anomaly_severity":    anomaly_severity,
            "anomaly_flags":       anomaly_flags,
            "is_anomalous":        is_anomalous,
            "anomaly_overridden":  anomaly_overridden,
            "final_risk_score":    final_risk_score,
            "anomaly_score":       anomaly_score_if,
            "fusion_explanation":  fusion_explanation,
            "risk_boost":          risk_boost,
        }

    def _build_fusion_explanation(
        self,
        m1_level: str, m1_explanation: str,
        final_level: str, anomaly_severity: str, anomaly_flags: list,
        anomaly_expl: str, anomaly_overridden: bool, risk_boost: int
    ) -> str:
        """Génère l'explication finale complète combinant les deux modèles."""

        level_emoji = {"BASE": "🟢", "SENSITIVE": "🟡", "CRITICAL": "[HIGH]"}.get(final_level, "⚪")
        sev_emoji   = {"NONE": "[OK]", "LOW": "[!]", "MEDIUM": "[MED]", "HIGH": "[HIGH]", "CRITICAL": "[ALERT]"}.get(anomaly_severity, "[!]")

        lines = [
            "═══════════════════════════════════════════",
            f" DÉCISION FUSIONNÉE : {level_emoji} {final_level}",
            "═══════════════════════════════════════════",
            "",
            "── MODÈLE 1 : Classification Hybride ──────",
            f"Niveau initial : {m1_level}",
            m1_explanation.strip(),
            "",
            "── MODÈLE 2 : Anomalies Comportementales ──",
            f"{sev_emoji} Sévérité anomalie : {anomaly_severity}",
        ]

        if anomaly_flags:
            clean_flags = []
            for f in anomaly_flags:
                key = f.split(":")[0].replace("ANOMALY_", "").replace("_", " ").title()
                detail = f.split(":")[1] if ":" in f else ""
                clean_flags.append(f"  • {key} : {detail}")
            lines.extend(clean_flags)
        else:
            lines.append("  • Aucune anomalie comportementale détectée")

        lines.append(anomaly_expl.strip())

        if anomaly_overridden:
            lines.extend([
                "",
                f"⚡ OVERRIDE ANOMALIE : Modèle 1 donnait {m1_level}, "
                f"mais l'anomalie ({anomaly_severity}) force le niveau à {final_level}.",
                f"   Score de risque augmenté de +{risk_boost} pts.",
            ])
        elif risk_boost > 0:
            lines.extend([
                "",
                f"[UP] Anomalie détectée : +{risk_boost} pts ajoutés au score de risque.",
                f"   Niveau maintenu à {final_level} (déjà suffisamment élevé).",
            ])

        return "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────
decision_fusion_service = DecisionFusionService()