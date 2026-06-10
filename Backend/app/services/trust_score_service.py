# app/services/trust_score_service.py
"""
Service Trust Score (Réputation Employé) — V3.0
=================================================
Calcule un score de réputation 0-100 pour chaque employé basé sur
son historique de demandes d'accès approuvées/rejetées.

Formule :
  score = 100
        + (nb_approuvés × 3)
        - (nb_critiques_demandées × 5)   ← proxy de comportement à risque
  Score clampé entre 0 et 100.

  Note : les rejets ne pénalisent plus le score (supprimé volontairement).

Labels :
  ≥ 75 → FIABLE    (vert)   : l'IA peut être plus souple
  ≥ 45 → NEUTRE    (orange) : comportement standard
  < 45 → SUSPECT   (rouge)  : l'IA doit être plus stricte
"""

from sqlalchemy.orm import Session
from typing import Optional


class TrustScoreService:

    # Poids de la formule
    APPROVE_BONUS      = 3      # Par approbation reçue
    CRITICAL_PENALTY   = 5      # Par demande de niveau CRITICAL faite
    SENSITIVE_PENALTY  = 1      # Par demande SENSITIVE
    # REJECT_PENALTY supprimé : un refus ne pénalise plus le score

    # Seuils de label
    FIABLE_THRESHOLD   = 75
    SUSPECT_THRESHOLD  = 45

    def compute_trust_score(self, employee_id: str, db: Session) -> dict:
        """
        Calcule et retourne le Trust Score complet de l'employé.
        Met à jour la colonne trust_score en DB.
        """
        from app.models.ticket import Ticket, TicketStatus
        from app.models.classification_result import ClassificationResult
        from app.models.employee import Employee

        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return self._default_score()

        # Récupérer tous les tickets de cet employé
        tickets = db.query(Ticket).filter(Ticket.employee_id == employee_id).all()

        rejected_count  = sum(1 for t in tickets if t.status == TicketStatus.REJECTED)
        approved_count  = sum(1 for t in tickets if t.status == TicketStatus.APPROVED)
        total_requests  = len(tickets)

        # Compter les demandes critiques via les classifications IA
        critical_count  = 0
        sensitive_count = 0
        for t in tickets:
            cls = t.classification
            if cls:
                if cls.predicted_level == "CRITICAL":
                    critical_count += 1
                elif cls.predicted_level == "SENSITIVE":
                    sensitive_count += 1

        # Calcul du score (les rejets ne pénalisent plus)
        score = 100
        score += approved_count  * self.APPROVE_BONUS
        score -= critical_count  * self.CRITICAL_PENALTY
        score -= sensitive_count * self.SENSITIVE_PENALTY

        # Clamp 0-100
        score = max(0, min(100, score))

        # Mise à jour en DB si les colonnes existent
        try:
            employee.trust_score        = float(score)
            employee.total_requests     = total_requests
            employee.rejected_requests  = rejected_count
            employee.approved_requests  = approved_count
            db.flush()
        except Exception:
            pass  # Colonnes pas encore migrées → ignorer silencieusement

        label = self.get_trust_label(score)

        return {
            "employee_id":      employee_id,
            "trust_score":      score,
            "trust_label":      label,
            "total_requests":   total_requests,
            "approved":         approved_count,
            "rejected":         rejected_count,
            "critical_demands": critical_count,
            "risk_modifier":    self.score_to_risk_modifier(score),
        }

    def get_trust_label(self, score: float) -> str:
        if score >= self.FIABLE_THRESHOLD:
            return "FIABLE"
        elif score >= self.SUSPECT_THRESHOLD:
            return "NEUTRE"
        else:
            return "SUSPECT"

    def score_to_risk_modifier(self, trust_score: float) -> int:
        """
        Convertit le Trust Score en modificateur de risque pour l'IA.
        Un employé SUSPECT → l'IA ajoute des points de risque.
        Un employé FIABLE  → l'IA réduit légèrement les points de risque.
        """
        if trust_score < 20:
            return +30   # Très suspect → aggrave fortement
        elif trust_score < self.SUSPECT_THRESHOLD:
            return +15
        elif trust_score < self.FIABLE_THRESHOLD:
            return 0     # Neutre → pas de modification
        elif trust_score < 90:
            return -5    # Fiable → légère réduction
        else:
            return -10   # Très fiable → réduction

    def update_after_decision(self, employee_id: str, decision: str, db: Session):
        """
        Appelé après chaque approbation/rejet pour recalculer le score.
        decision: 'approved' | 'rejected'
        """
        if not employee_id:
            return
        try:
            result = self.compute_trust_score(employee_id, db)
            print(
                f"🏅 [TRUST] Employé {employee_id} : "
                f"Score={result['trust_score']} ({result['trust_label']}) "
                f"après décision '{decision}'"
            )
        except Exception as e:
            print(f"[!] [TRUST] Erreur mise  jour trust score {employee_id}: {e}")

    def _default_score(self) -> dict:
        return {
            "employee_id":      None,
            "trust_score":      100.0,
            "trust_label":      "NEUTRE",
            "total_requests":   0,
            "approved":         0,
            "rejected":         0,
            "critical_demands": 0,
            "risk_modifier":    0,
        }


# Singleton
trust_score_service = TrustScoreService()