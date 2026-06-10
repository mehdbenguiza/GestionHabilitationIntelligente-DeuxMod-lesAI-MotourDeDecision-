# app/services/anomaly_service.py
"""
Service de Détection d'Anomalies Comportementales — Modèle 2
=============================================================
Combine deux approches complémentaires :
  1. Règles métier explicites (hors horaire, weekend, volume)
  2. Isolation Forest (ML non-supervisé) pour les patterns inhabituels

Règles métier :
  - Horaires autorisés : 07h00 – 18h00 (lundi–vendredi)
  - Samedi & Dimanche  : ANOMALY_WEEKEND_SUBMISSION
  - Hors 07h-18h       : ANOMALY_OUT_OF_HOURS
  - Volume tickets/jour : 4-5 → LOW | 6-7 → MEDIUM | 8+ → HIGH

IMPORTANT :
  Les tickets avec source="ADMIN_SIMULATION" sont EXCLUS de toute analyse.
"""

import os
import joblib
import numpy as np
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy.orm import Session


# ─── Constantes Horaires ────────────────────────────────────────────────────
WORK_START_HOUR = 7    # 07h00 (marge -1h sur 08h00)
WORK_END_HOUR   = 18   # 18h00 (marge +1h sur 17h00)
WORK_DAYS       = {0, 1, 2, 3, 4}  # 0=Lundi … 4=Vendredi

# ─── Seuils volume tickets / jour ───────────────────────────────────────────
VOLUME_NORMAL_MAX  = 3   # ≤ 3 : normal
VOLUME_LOW_MAX     = 5   # 4-5 : LOW
VOLUME_MEDIUM_MAX  = 7   # 6-7 : MEDIUM
                          # 8+  : HIGH

# ─── Mapping sévérité → niveau de risque ajouté ─────────────────────────────
SEVERITY_RISK_BOOST = {
    "NONE":     0,
    "LOW":     10,
    "MEDIUM":  25,
    "HIGH":    50,
    "CRITICAL": 80,
}


class AnomalyService:

    def __init__(self):
        self._model  = None   # Isolation Forest
        self._scaler = None   # StandardScaler
        self._loaded = False

    # ─────────────────────────────────────────────────────────────────────────
    # Chargement du modèle ML
    # ─────────────────────────────────────────────────────────────────────────

    def load_model(self):
        """Charge l'Isolation Forest depuis models/anomaly_detector.pkl"""
        try:
            base   = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            m_path = os.path.join(base, "models", "anomaly_detector.pkl")
            s_path = os.path.join(base, "models", "anomaly_scaler.pkl")

            if os.path.exists(m_path) and os.path.exists(s_path):
                self._model  = joblib.load(m_path)
                self._scaler = joblib.load(s_path)
                self._loaded = True
                print("INFO: Modele anomalie (Isolation Forest) charge")
            else:
                print("WARNING: anomaly_detector.pkl introuvable  mode rgles seules activ")
        except Exception as e:
            print(f"ERROR: Chargement modle anomalie : {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Point d'entrée principal
    # ─────────────────────────────────────────────────────────────────────────

    def analyze_ticket(self, ticket, db: Session) -> dict:
        """
        Analyse complète d'un ticket pour détecter des anomalies comportementales.

        Retourne un dict :
        {
          "is_anomalous": bool,
          "severity": "NONE"|"LOW"|"MEDIUM"|"HIGH"|"CRITICAL",
          "flags": ["ANOMALY_OUT_OF_HOURS", ...],
          "anomaly_score": float | None,   # Score IF (-1 anormal, +1 normal)
          "risk_boost": int,               # Points à ajouter au score de risque
          "explanation": str,
          "context": { "hour": int, "weekday": int, "tickets_today": int, ... }
        }
        """
        # ── Règle prioritaire : exclure les simulations admin ────────────────
        ticket_source = getattr(ticket, "source", "ITOP") or "ITOP"
        if ticket_source == "ADMIN_SIMULATION":
            return self._no_anomaly(reason="Simulation admin exclue de l'analyse", source=ticket_source)

        # ── Déterminer le timestamp de référence ─────────────────────────────
        submitted_at = getattr(ticket, "employee_submitted_at", None) or getattr(ticket, "created_at", None)
        if submitted_at is None:
            submitted_at = datetime.now(timezone.utc)

        hour    = submitted_at.hour
        weekday = submitted_at.weekday()   # 0=Lundi … 6=Dimanche
        is_weekend    = weekday >= 5
        is_out_of_hours = not (WORK_START_HOUR <= hour < WORK_END_HOUR)

        # ── Comptage des tickets de l'employé aujourd'hui ────────────────────
        tickets_today = self._count_tickets_today(ticket, db, submitted_at.date())
        tickets_week  = self._count_tickets_week(ticket, db, submitted_at)

        # ── Analyse par règles métier ────────────────────────────────────────
        flags = []

        if is_weekend:
            day_name = "Samedi" if weekday == 5 else "Dimanche"
            flags.append(f"ANOMALY_WEEKEND_SUBMISSION:{day_name}")

        if is_out_of_hours:
            period = "nuit" if hour < WORK_START_HOUR or hour >= 22 else "soirée"
            flags.append(f"ANOMALY_OUT_OF_HOURS:{hour:02d}h{submitted_at.minute:02d}")

        if tickets_today > VOLUME_MEDIUM_MAX:
            flags.append(f"ANOMALY_HIGH_VOLUME_HIGH:{tickets_today}_tickets_ce_jour")
        elif tickets_today > VOLUME_LOW_MAX:
            flags.append(f"ANOMALY_HIGH_VOLUME_MEDIUM:{tickets_today}_tickets_ce_jour")
        elif tickets_today > VOLUME_NORMAL_MAX:
            flags.append(f"ANOMALY_HIGH_VOLUME_LOW:{tickets_today}_tickets_ce_jour")

        # ── Score Isolation Forest ───────────────────────────────────────────
        anomaly_score = None
        if self._loaded:
            anomaly_score = self._compute_if_score(
                hour, weekday, is_weekend, is_out_of_hours, tickets_today, tickets_week
            )
            # Isolation Forest : Decision Function renvoie > 0 pour normal, < 0 pour anomalie.
            # On déclenche un flag ML si le score est significativement négatif.
            if anomaly_score < -0.05 and not flags:
                flags.append(f"ANOMALY_ML_PATTERN:score={anomaly_score:.3f}")

        # ── Calcul de la sévérité ────────────────────────────────────────────
        severity = self._compute_severity(flags, anomaly_score, is_weekend, is_out_of_hours, tickets_today)
        is_anomalous = severity != "NONE"

        # ── Explication lisible ──────────────────────────────────────────────
        explanation = self._build_explanation(flags, severity, hour, weekday, tickets_today, anomaly_score)

        context = {
            "submitted_at":   submitted_at.isoformat(),
            "hour":           hour,
            "weekday":        weekday,
            "is_weekend":     is_weekend,
            "is_out_of_hours": is_out_of_hours,
            "tickets_today":  tickets_today,
            "tickets_week":   tickets_week,
        }

        result = {
            "is_anomalous":  is_anomalous,
            "severity":      severity,
            "flags":         flags,
            "anomaly_score": round(anomaly_score, 4) if anomaly_score is not None else None,
            "risk_boost":    SEVERITY_RISK_BOOST.get(severity, 0),
            "explanation":   explanation,
            "context":       context,
            "ticket_source": ticket_source,
        }

        # ── Persistance en base ──────────────────────────────────────────────
        self._save_log(db, ticket, result, context)

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Calcul du score Isolation Forest
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_if_score(self, hour, weekday, is_weekend, is_out_of_hours, tickets_today, tickets_week) -> float:
        """Retourne le score IF. Valeurs négatives = anormal."""
        try:
            features = np.array([[
                hour,
                weekday,
                int(is_weekend),
                int(is_out_of_hours),
                tickets_today,
                tickets_week,
            ]], dtype=float)
            scaled = self._scaler.transform(features)
            # decision_function retourne des valeurs > 0 pour les inliers et < 0 pour les outliers.
            # La plage est typiquement [-0.5, 0.5].
            score = float(self._model.decision_function(scaled)[0])
            return score
        except Exception as e:
            print(f"WARNING: IF score error: {e}")
            return 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # Calcul de la sévérité
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_severity(self, flags, anomaly_score, is_weekend, is_out_of_hours, tickets_today) -> str:
        """Détermine la sévérité globale selon les flags et le score IF."""
        if not flags and (anomaly_score is None or anomaly_score >= -0.05):
            return "NONE"

        # Combinaison de plusieurs anomalies → sévérité maximale
        critical_flags = [f for f in flags if "HIGH" in f or ("WEEKEND" in f and "OUT_OF_HOURS" in f)]
        high_flags     = [f for f in flags if "MEDIUM" in f or ("WEEKEND" in f and tickets_today > VOLUME_NORMAL_MAX)]
        medium_flags   = [f for f in flags if "LOW" in f or "OUT_OF_HOURS" in f or "WEEKEND" in f]

        # Score IF très négatif = booste la sévérité
        if anomaly_score is not None and anomaly_score < -0.3:
            if critical_flags or (len(flags) >= 2):
                return "CRITICAL"
            return "HIGH"

        if critical_flags or len(flags) >= 3:
            return "CRITICAL"
        if high_flags or len(flags) >= 2:
            return "HIGH"
        if medium_flags:
            # Weekend seul un jour ouvrable tardif → MEDIUM
            if is_weekend and is_out_of_hours:
                return "HIGH"
            if is_weekend or (is_out_of_hours and tickets_today > VOLUME_NORMAL_MAX):
                return "MEDIUM"
            return "LOW"

        return "LOW" if flags else "NONE"

    # ─────────────────────────────────────────────────────────────────────────
    # Explication lisible
    # ─────────────────────────────────────────────────────────────────────────

    def _build_explanation(self, flags, severity, hour, weekday, tickets_today, anomaly_score) -> str:
        if not flags:
            return "[OK] Aucune anomalie comportementale détectée."

        day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        day_name  = day_names[weekday] if 0 <= weekday < 7 else "?"

        sev_label = {
            "LOW":      "[!] Anomalie légère",
            "MEDIUM":   "[MED] Anomalie modérée",
            "HIGH":     "[HIGH] Anomalie sérieuse",
            "CRITICAL": "[ALERT] Anomalie critique",
        }.get(severity, "[!] Anomalie")

        lines = [f"{sev_label}  {len(flags)} signal(s) dtect(s) :"]

        for flag in flags:
            key = flag.split(":")[0]
            detail = flag.split(":")[1] if ":" in flag else ""
            label_map = {
                "ANOMALY_WEEKEND_SUBMISSION":    f"[DATE] Soumission le {detail} (jour non ouvré)",
                "ANOMALY_OUT_OF_HOURS":          f"[NIGHT] Soumission hors horaires ({detail})",
                "ANOMALY_HIGH_VOLUME_LOW":       f"[STATS] Volume inhabituel : {detail.replace('_', ' ')}",
                "ANOMALY_HIGH_VOLUME_MEDIUM":    f"[STATS] Volume suspect : {detail.replace('_', ' ')}",
                "ANOMALY_HIGH_VOLUME_HIGH":      f"[STATS] Volume critique : {detail.replace('_', ' ')}",
                "ANOMALY_ML_PATTERN":            f"[AI] Pattern inhabituel détecté par l'IA ({detail})",
            }
            lines.append(f"   {label_map.get(key, flag)}")

        if anomaly_score is not None:
            lines.append(f"\n[UP] Score Isolation Forest : {anomaly_score:.4f} (< 0 = suspect)")

        lines.append(f"\nContexte : {day_name} {hour:02d}h, {tickets_today} ticket(s) soumis ce jour")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Comptages DB
    # ─────────────────────────────────────────────────────────────────────────

    def _count_tickets_today(self, ticket, db: Session, ref_date: date) -> int:
        """Compte les tickets soumis par cet employé à la même date."""
        try:
            from app.models.ticket import Ticket
            from sqlalchemy import func as sqlfunc, cast, Date
            employee_id = getattr(ticket, "employee_id", None)
            if not employee_id:
                return 1
            count = (
                db.query(Ticket)
                .filter(
                    Ticket.employee_id == employee_id,
                    Ticket.source != "ADMIN_SIMULATION",
                    sqlfunc.date(Ticket.employee_submitted_at) == ref_date,
                )
                .count()
            )
            return max(1, count)
        except Exception:
            return 1

    def _count_tickets_week(self, ticket, db: Session, ref_dt: datetime) -> int:
        """Compte les tickets de l'employé sur les 7 derniers jours."""
        try:
            from app.models.ticket import Ticket
            from datetime import timedelta
            employee_id = getattr(ticket, "employee_id", None)
            if not employee_id:
                return 1
            week_ago = ref_dt - timedelta(days=7)
            count = (
                db.query(Ticket)
                .filter(
                    Ticket.employee_id == employee_id,
                    Ticket.source != "ADMIN_SIMULATION",
                    Ticket.employee_submitted_at >= week_ago,
                )
                .count()
            )
            return max(1, count)
        except Exception:
            return 1

    # ─────────────────────────────────────────────────────────────────────────
    # Persistance AnomalyLog
    # ─────────────────────────────────────────────────────────────────────────

    def _save_log(self, db: Session, ticket, result: dict, context: dict):
        """Sauvegarde le résultat d'analyse dans la table anomaly_logs."""
        try:
            from app.models.anomaly_log import AnomalyLog
            log = AnomalyLog(
                ticket_id          = ticket.id,
                employee_id        = getattr(ticket, "employee_id", None),
                anomaly_score      = result.get("anomaly_score"),
                is_anomalous       = result["is_anomalous"],
                anomaly_flags      = result["flags"],
                severity           = result["severity"],
                submission_hour    = context.get("hour"),
                submission_weekday = context.get("weekday"),
                is_weekend         = context.get("is_weekend"),
                is_out_of_hours    = context.get("is_out_of_hours"),
                tickets_today      = context.get("tickets_today"),
                explanation        = result["explanation"],
                ticket_source      = result.get("ticket_source", "ITOP"),
            )
            db.add(log)
            db.flush()
        except Exception as e:
            print(f"WARNING: Impossible de sauvegarder AnomalyLog: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Résultat vide (pas d'anomalie)
    # ─────────────────────────────────────────────────────────────────────────

    def _no_anomaly(self, reason: str = "", source: str = "ITOP") -> dict:
        return {
            "is_anomalous":  False,
            "severity":      "NONE",
            "flags":         [],
            "anomaly_score": None,
            "risk_boost":    0,
            "explanation":   f"[OK] {reason}" if reason else "[OK] Aucune anomalie dtecte.",
            "context":       {},
            "ticket_source": source,
        }


# ── Singleton ────────────────────────────────────────────────────────────────
anomaly_service = AnomalyService()