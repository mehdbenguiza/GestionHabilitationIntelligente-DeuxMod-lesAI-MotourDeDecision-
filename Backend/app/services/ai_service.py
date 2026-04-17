# app/services/ai_service.py

import joblib
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.feature_extractor import FeatureExtractor
from app.models.classification_result import ClassificationResult
from app.models.decision_engine import DecisionEngine
from app.models.ticket import Ticket, TicketStatus
from app.services.audit_service import audit_service

# ─────────────────────────────────────────────────────────────────────────────
# Constantes partagées (Alignées sur le nouveau generator)
# ─────────────────────────────────────────────────────────────────────────────

CRITICAL_APPS   = {"SWIFT", "T24", "MUREX"}
SENSITIVE_APPS  = {"AML_TIDE", "E_BANKING"}
PRODUCTION_ENVS = {"PRD"}
CRITICAL_ENVS   = {"INV", "CRT", "UAT"}
DBA_ACCESS      = "DBA_ACCESS"
CRITICAL_ACCESS = {"DELETE", "DBA_ACCESS", "FULL_ACCESS"}
WRITE_ACCESS    = {"WRITE", "UPDATE", "DELETE"}
CRITICAL_RES    = {"DONNEES_CLIENTS_SENSIBLES", "TRANSACTIONS_FINANCIERES", "CLEFS_CRYPTOGRAPHIQUES"}
SENSITIVE_RES   = {"LOGS_SECURITE", "CODE_SOURCE", "DONNEES_CARRIERES_RH"}

# Libellés lisibles pour l'UX (Requirement 4)
RISK_LABEL_VERBOSE = {
    "BASE": "Faible risque",
    "SENSITIVE": "Risque modéré",
    "CRITICAL": "Risque élevé"
}

def _build_risk_breakdown(ticket_data: dict) -> tuple[dict, int]:
    """
    Calcule le score de risque facteur par facteur.
    Implémentation des règles expertes 1.1 à 1.10.
    Retourne (facteurs, score_total).
    """
    app    = ticket_data.get("application", "").upper()
    env    = ticket_data.get("environment", "").upper()
    access = ticket_data.get("access_type", "").upper()
    res    = ticket_data.get("resource", "").upper()
    role   = ticket_data.get("role", "").upper()
    senior = ticket_data.get("user_seniority", "senior")
    reason = ticket_data.get("request_reason", "")
    approval = ticket_data.get("manager_approval_status", "none")
    team   = ticket_data.get("team", "").upper()

    factors = {}   # facteur → (points, description)
    risk_score = 0
    is_sensitive_res = res in CRITICAL_RES

    # 1. APPLICATION & ENVIRONNEMENT (1.1, 1.2)
    if app in CRITICAL_APPS:
        risk_score += 30
        factors["application"] = (30, f"Application hautement critique ({app})")
    elif app in SENSITIVE_APPS:
        risk_score += 20
        factors["application"] = (20, f"Application sensible ({app})")

    if env == "PRD":
        risk_score += 50 # Requirement 6: Corrected from 40 to 50
        factors["environment"] = (50, "Environnement de PRODUCTION (Risque maximal)")
        
        # Requirement 7: Cas critique PRD + DELETE
        if access in {"DELETE", "DBA_ACCESS"}:
            risk_score += 30
            factors["prd_delete_combo"] = (30, "Suppression/DBA en production (Risque extrême)")

        if access == "FULL_ACCESS":
            risk_score += 60 # 1.2
            factors["crit_prd_full"] = (60, "FULL_ACCESS en PRD : Interdit hors procédure d'urgence")
        if access == "READ" and is_sensitive_res:
             risk_score += 30 # 1.1
             factors["crit_prd_read_sens"] = (30, "Consultation de données sensibles en PRD")
    elif env in CRITICAL_ENVS:
        risk_score += 20
        factors["environment"] = (20, f"Environnement de pré-production ({env})")
    else:
        if access == "FULL_ACCESS":
            risk_score += 15 # 1.2
            factors["dev_full_access"] = (15, "Accès étendu sur environnement de développement")

    # 2. TYPE D'ACCÈS & DBA (1.8)
    if access == "DBA_ACCESS":
        risk_score += 50
        factors["dba_access"] = (50, "Accès ADMINISTRATEUR BASE DE DONNÉES (DBA)")
    elif access in {"DELETE", "FULL_ACCESS"}:
        risk_score += 40
        factors["destructive_access"] = (40, f"Accès à haut pouvoir ({access})")
    elif access in {"WRITE", "UPDATE"}:
        risk_score += 20
        factors["write_access"] = (20, "Accès en modification/écriture")

    # 3. RESSOURCE & RH (1.9)
    if is_sensitive_res:
        risk_score += 30
        factors["resource_sens"] = (30, f"Ressource critique ({res})")
    elif res == "DONNEES_CARRIERES_RH":
        risk_score += 20
        factors["resource_rh"] = (20, "Données confidentielles RH (Carrières)")

    # 4. SÉNIORITÉ (1.4)
    if senior == "junior":
        if env == "PRD":
            risk_score += 25
            factors["junior_risk"] = (25, "Profil JUNIOR manipulant la production")
        else:
            risk_score += 5
            factors["junior_note"] = (5, "Profil junior (contexte hors-prod)")
    elif senior == "senior" and env == "PRD" and access == "FULL_ACCESS":
        risk_score += 40
        factors["senior_crit"] = (40, "Action critique PRD par un profil Senior")

    # 5. LOGIQUE PAR ÉQUIPE (1.5, 1.6, 1.7)
    if team == "MOA" and access != "READ":
        risk_score += 25
        factors["moa_mismatch"] = (25, "Équipe MOA demandant un accès en écriture/admin")
    
    if team == "TRADING":
        if app not in {"MUREX", "T24"}:
            risk_score += 40 # 1.6
            factors["trading_out_scope"] = (40, f"Profil Trader hors périmètre métier ({app})")
        if is_sensitive_res and access != "READ":
            risk_score += 30
            factors["trading_sens_write"] = (30, "Modification de données financières par un Trader")

    if team == "SECURITE" and env == "PRD" and access in CRITICAL_ACCESS:
        risk_score += 40
        factors["secu_prd_action"] = (40, "Action d'administration PRD par la Sécurité")

    if role in {"DEVELOPPEUR", "STAGIAIRE"} and env == "PRD":
        # 1.7 DEV en PRD
        if not (reason == "incident_production_bloquant" and approval == "approved"):
            risk_score += 30
            factors["dev_in_prd"] = (30, "Développeur accédant à la production (Hors incident validé)")

    # 6. JUSTIFICATION & MODÉRATEURS (1.10, 1.3)
    if reason == "incident_production_bloquant":
        if approval == "approved":
            risk_score -= 10
            factors["incident_legit"] = (-10, "Incident production bloquant validé par Manager")
        else:
            risk_score += 20
            factors["incident_unauth"] = (20, "Accès incident production SANS validation préalable")
    elif reason == "audit_reglementaire_bct":
        risk_score -= 15
        factors["audit_bct"] = (-15, "Contexte d'audit réglementaire BCT")
    elif reason == "demande_metier_urgente":
        risk_score += 10
        factors["urgent_request"] = (10, "Demande marquée comme urgente par l'utilisateur")

    # 1.3 : Approval ignoré si score trop élevé
    if approval == "approved":
        if risk_score < 85:
            risk_score -= 20
            factors["manager_ok"] = (-20, "Validation explicite par le manager direct")
        else:
            factors["manager_ignored"] = (0, "⚠ Validation manager ignorée : Risque intrinsèque trop élevé")

    return factors, risk_score


def _build_explanation(level: str, factors: dict, confidence: float, source: str = "model") -> str:
    """
    Génère une explication triée par importance avec note de cohérence (Requirement 1, 3, 4, 8).
    """
    risk_label = RISK_LABEL_VERBOSE.get(level, "Niveau indéterminé")
    total_score = sum([v[0] for v in factors.values()])
    
    # Requirement 3: Tri par importance (valeur absolue des points)
    sorted_items = sorted(
        factors.items(),
        key=lambda x: abs(x[1][0]),
        reverse=True
    )

    # Requirement 8 & 10 (v2.0): Niveaux de confiance pro
    if confidence < 0.60:
        confidence_note = "📌 Note : Faible confiance - décision incertaine (analyse ML divergente)"
    elif confidence < 0.80:
        confidence_note = "✅ Note : Confiance modérée"
    else:
        confidence_note = "🚀 Note : Décision fiable (forte cohérence IA/Métier)"

    lines = []
    # Afficher les 4 plus gros facteurs
    for _, (pts, desc) in sorted_items[:4]:
        sign = "+" if pts >= 0 else ""
        lines.append(f"• {desc} ({sign}{pts} pts)")

    suffix = ""
    if source == "human_correction":
        suffix = "\n⚠️ Classification imposée par la bibliothèque d'expertise humaine."

    return (
        f"STATUT : {risk_label} ({level})\n"
        f"Score de risque : {total_score} pts\n"
        f"Confiance IA : {confidence * 100:.1f}%\n"
        + "\n".join(lines) + "\n\n"
        + confidence_note
        + suffix
    )


class AIService:
    def __init__(self):
        self.model = None
        self.extractor = None
        self.is_loaded = False
        self.model_version = "2.0.0" # Upgrade version

    def load_models(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            models_dir = os.path.join(base_dir, "models")
            
            extractor_path = os.path.join(models_dir, "feature_extractor.pkl")
            self.extractor = FeatureExtractor()
            self.extractor.load(extractor_path)
            
            model_path = os.path.join(models_dir, "classifier_model.pkl")
            self.model = joblib.load(model_path)
            self.is_loaded = True
            print(f"INFO: Modèles IA v{self.model_version} chargés avec succès")
            return True
        except Exception as e:
            print(f"ERROR: Échec chargement IA : {e}")
            return False

    def check_corrections(self, db: Session, ticket_data: dict) -> dict | None:
        """Consulte la bibliothèque de corrections expertes."""
        try:
            from app.models.ai_feedback import AICorrection, compute_profile_signature
            sig = compute_profile_signature(
                application  = ticket_data.get("application", ""),
                environment  = ticket_data.get("environment", ""),
                access_type  = ticket_data.get("access_type", ""),
                team         = ticket_data.get("team", ""),
                resource     = ticket_data.get("resource", ""),
            )
            correction = db.query(AICorrection).filter(AICorrection.profile_signature == sig).first()
            if correction:
                correction.usage_count = (correction.usage_count or 0) + 1
                correction.last_used_at = datetime.utcnow()
                db.flush()

                level = correction.corrected_level
                factors, score = _build_risk_breakdown(ticket_data)
                return {
                    "level":        level,
                    "risk_level":   level,
                    "risk_score":   score,
                    "risk_label":   RISK_LABEL_VERBOSE.get(level, level),
                    "confidence":   100.0,
                    "probabilities": { "BASE": 100.0 if level=="BASE" else 0.0, "SENSITIVE": 100.0 if level=="SENSITIVE" else 0.0, "CRITICAL": 100.0 if level=="CRITICAL" else 0.0 },
                    "explanation":  correction.corrected_reason,
                    "details":      factors,
                    "source":       "human_correction",
                }
        except Exception as e:
            print(f"WARNING: Erreur check_corrections: {e}")
        return None

    def classify_ticket_data(self, ticket_data: dict) -> dict:
        """Classifie et explique (Requirement 2 & v2.0 Hybride)"""
        factors, score = _build_risk_breakdown(ticket_data)
        
        # v2.0 : Déterminer le niveau via les règles (Expertise pure)
        rule_level = "BASE"
        if score >= 85: rule_level = "CRITICAL"
        elif score >= 50: rule_level = "SENSITIVE"

        if not self.is_loaded:
             # Fallback heuristique pure si pas de modèle
             return {
                "level": rule_level,
                "prediction": rule_level,
                "risk_level": rule_level,
                "risk_score": score,
                "risk_score_rules": score,
                "risk_label": RISK_LABEL_VERBOSE.get(rule_level, rule_level),
                "confidence": 70.0,
                "confidence_level": "✅ Confiance modérée (Règles métier)",
                "explanation": _build_explanation(rule_level, factors, 0.7, source="fallback"),
                "details": factors,
                "triggered_rules": [f"{desc} ({pts} pts)" for _, (pts, desc) in factors.items()],
                "decision_source": "RULES_ONLY (Fallback)",
                "consistency": {"status": "OK", "message": "Mode dégradé active"},
                "recommended_action": "MANUAL_REVIEW" if rule_level != "BASE" else "AUTO_APPROVE",
                "source": "fallback",
             }

        try:
            features_df  = self.extractor.transform_single_ticket(ticket_data)
            prediction   = self.model.predict(features_df)[0]
            probabilities= self.model.predict_proba(features_df)[0]
            confidence   = round(max(probabilities) * 100, 2)

            classes   = self.model.classes_.tolist()
            prob_dict = {
                "BASE":      round(probabilities[classes.index("BASE")] * 100, 2),
                "SENSITIVE": round(probabilities[classes.index("SENSITIVE")] * 100, 2),
                "CRITICAL":  round(probabilities[classes.index("CRITICAL")] * 100, 2),
            }

            # Requirement 1 (v2.0): Vérifier cohérence
            consistency = "OK"
            consistency_msg = "ML et règles métiers alignés"
            if prediction != rule_level:
                consistency = "WARNING"
                consistency_msg = f"Incohérence détectée : ML={prediction} vs RULES={rule_level}"

            # Requirement 4 & 10 (v2.0): Confidence nuance
            if confidence < 50:
                warning_label = "⚠ Très faible confiance IA"
            elif confidence < 70:
                warning_label = "⚠ Confiance modérée"
            else:
                warning_label = "✅ Confiance élevée"

            explanation = _build_explanation(prediction, factors, confidence/100, source="model")
            
            return {
                "level":        prediction,
                "prediction":   prediction,
                "rule_based_level": rule_level,
                "risk_level":   prediction,
                "risk_score":   score,
                "risk_score_rules": score,
                "risk_label":   RISK_LABEL_VERBOSE.get(prediction, prediction),
                "confidence":   confidence,
                "confidence_level": warning_label,
                "probabilities": prob_dict,
                "explanation":  explanation,
                "details":      factors,
                "triggered_rules": [f"{desc} ({'+' if pts > 0 else ''}{pts} pts)" for _, (pts, desc) in factors.items()],
                "decision_source": "HYBRID (ML + RULES)",
                "consistency": {
                    "status": consistency,
                    "message": consistency_msg
                },
                "recommended_action": self._pre_determine_action(prediction, confidence, consistency, score),
                "source":       "model",
            }
        except Exception as e:
            print(f"ERROR classification: {e}")
            return { "level": "BASE", "risk_level": "BASE", "risk_score": 0, "confidence": 50.0, "probabilities": {}, "explanation": "Erreur technique IA.", "source": "error", "details": {} }

    def _pre_determine_action(self, prediction, confidence, consistency, score) -> str:
        """Détermine l'action recommandée selon la matrice de risque pro."""
        # Fail-safe (Requirement 5 & 7 v2.0)
        if confidence < 50 or consistency == "WARNING":
            return "MANUAL_REVIEW"
        
        if prediction == "CRITICAL" or score >= 85:
            return "BLOCK" if score > 150 else "MANUAL_REVIEW"
        
        if prediction == "SENSITIVE":
            return "MANUAL_REVIEW"
            
        return "AUTO_APPROVE"

    def classify_ticket_model(self, ticket: Ticket, db: Session | None = None) -> dict:
        """Point d'entrée principal via objet SQLAlchemy"""
        details  = self._get_details(ticket)

        # ✅ Lire la séniorité RÉELLE depuis la table employees
        # Le JSON du ticket peut être absent ou erroné — la DB est la source de vérité
        employee_seniority = details.get("user_seniority", "junior")
        if db is not None and ticket.employee_id:
            try:
                from app.models.employee import Employee
                emp = db.query(Employee).filter(Employee.id == ticket.employee_id).first()
                if emp and emp.seniority:
                    employee_seniority = emp.seniority
            except Exception as e:
                print(f"WARNING: Impossible de lire la seniorite employee {ticket.employee_id}: {e}")

        ticket_data = {
            "team":                    ticket.team_name or "MOE",
            "role":                    self._extract_role(ticket),
            "application":             self._extract_application(ticket),
            "environment":             self._extract_environment(ticket),
            "access_type":             self._extract_access_type(ticket),
            "resource":                self._extract_resource(ticket),
            "user_seniority":          employee_seniority,   
            "request_reason":          details.get("request_reason", "maintenance_preventive"),
            "manager_approval_status": details.get("manager_approval_status", "none"),
        }

        if db is not None:
            correction = self.check_corrections(db, ticket_data)
            if correction: return correction

        return self.classify_ticket_data(ticket_data)

    def classify_and_save(self, db: Session, ticket: Ticket) -> dict:
        """Effectue la classification, enregistre en base et applique la décision finale."""
        from app.models.audit_log import AuditLog

        result = self.classify_ticket_model(ticket, db=db)
        
        classification = ClassificationResult(
            ticket_id               = ticket.id,
            predicted_level         = result["level"],
            confidence              = result["confidence"],
            probabilities           = result.get("probabilities", {}),
            explanation             = result.get("explanation", ""),
            risk_factors            = result.get("details", {}),
            model_version           = self.model_version,
            source                  = result.get("source", "model"),
            
            # Nouveaux champs d'audit (v2.0)
            risk_score_rules        = result.get("risk_score_rules"),
            decision_source         = result.get("decision_source"),
            consistency_status      = result.get("consistency", {}).get("status"),
            consistency_message     = result.get("consistency", {}).get("message"),
            triggered_rules         = result.get("triggered_rules"),
            recommended_action      = result.get("recommended_action"),
            confidence_level_label  = result.get("confidence_level"),
            
            processed_at            = datetime.utcnow(),
        )
        db.add(classification)
        
        # 🔔 ALERTE : Création d'une notification via AuditService
        predicted = classification.predicted_level
        if predicted == "CRITICAL":
            audit_service.notify(
                db=db,
                title=f"ALERTE: Ticket Critique {ticket.ref}",
                message=f"Risque élevé détecté sur {ticket.ref} ({ticket.employee_name}). Validation immédiate requise.",
                type="danger"
            )
        elif predicted == "SENSITIVE":
            audit_service.notify(
                db=db,
                title=f"Alerte: Ticket Sensible {ticket.ref}",
                message=f"Le ticket {ticket.ref} demande une revue d'accès.",
                type="warning"
            )
        else:
            audit_service.notify(
                db=db,
                title=f"Info: Nouveau Ticket {ticket.ref}",
                message=f"Ticket de niveau BASE auto-analysé.",
                type="info"
            )
        print(f"[NOTIF] Notification créée pour le ticket {ticket.ref} ({predicted})")

        db.flush()

        # Enregistrer un Log d'Audit spécifique à l'IA via AuditService
        envs = getattr(ticket, 'requested_environments', ["Inconnu"])
        env_name = envs[0] if envs else "Inconnu"
        
        audit_service.log_action(
            db=db,
            ticket_id=ticket.id,
            ticket_ref=ticket.ref,
            acteur_name="Moteur IA Hybride",
            acteur_role="AI_ENGINE",
            action="Analyse IA Complétée",
            categorie="AI_AUDIT",
            environnement=env_name,
            resultat=classification.consistency_status,
            niveau_acces=classification.predicted_level,
            details={
                "score_metier": classification.risk_score_rules,
                "confidence_label": classification.confidence_level_label,
                "recommended_action": classification.recommended_action,
                "consistency_msg": classification.consistency_message
            }
        )

        decision = self._apply_decision_rules(result)

        decision_record = DecisionEngine(
            ticket_id          = ticket.id,
            classification_id  = classification.id,
            final_level        = result["level"],
            final_confidence   = result["confidence"],
            recommended_action = decision["action"],
            action_reason      = decision["reason"],
            rules_applied      = decision["rules_applied"],
            processed_at       = datetime.utcnow(),
        )
        db.add(decision_record)

        # Mise à jour du ticket (Shortcut pour Serializer)
        ticket.ai_risk_score = classification.risk_score_rules
        ticket.ai_consistency = classification.consistency_status
        ticket.ai_recommended_action = classification.recommended_action
        
        if decision["action"] == "AUTO_APPROVE":
            ticket.status = TicketStatus.APPROVED
            
            # --- Automatisation de la création du profil (Auto-Approbation) ---
            try:
                from app.services.profile_service import profile_service
                from app.services.itop_service import ITopService
                
                access_profile = profile_service.create_profile_from_ticket(
                    db          = db,
                    ticket      = ticket,
                    approved_by = "Moteur IA Automatique",
                )
                
                itop_srv = ITopService()
                system_name = access_profile.systeme.nom if access_profile.systeme else "Système cible"
                itop_srv.notify_ticket_approved(
                    ticket      = ticket,
                    profile     = access_profile,
                    system_name = system_name,
                    approved_by = "Moteur IA Automatique",
                )
                itop_srv.update_ticket_status(ticket.ref, "approved", "Auto-approbation de niveau BASE par l'IA.")
            except Exception as e:
                print(f"⚠️ [AUTO-APPROVE] Erreur lors de la création du profil automatisée pour {ticket.ref}: {e}")
            # ------------------------------------------------------------------
        elif decision["action"] == "ESCALATE_ADMIN":
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = "ADMIN"
        else:
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = "SUPER_ADMIN"

        ticket.assigned_at = datetime.utcnow()
        db.commit()

        return { "classification": result, "decision": decision }

    def _apply_decision_rules(self, result: dict) -> dict:
        level      = result["level"]
        confidence = result["confidence"]
        score      = result.get("risk_score", 0)
        action_rec = result.get("recommended_action", "MANUAL_REVIEW")
        consistency= result.get("consistency", {}).get("status", "OK")
        
        rules = ["hybrid_logic"]
        
        # Requirement 5 & 7 (v2.0) : Fail-safe
        if confidence < 50:
            return {
                "action": "ESCALATE_ADMIN",
                "reason": "Fail-safe: Confiance IA trop faible (< 50%) -> Analyse humaine requise.",
                "rules_applied": ["fail_safe_low_confidence"]
            }
            
        if consistency == "WARNING":
            return {
                "action": "ESCALATE_SUPER_ADMIN",
                "reason": f"Alerte de cohérence: Désaccord ML/Métier ({result['consistency']['message']})",
                "rules_applied": ["consistency_warning_escalation"]
            }

        # Logique de décision classique
        if action_rec == "BLOCK" or level == "CRITICAL" or score >= 85:
            return {"action": "ESCALATE_SUPER_ADMIN", "reason": "Risque élevé détecté ou action bloquante requise.", "rules_applied": rules + ["high_risk"]}
        
        if action_rec == "MANUAL_REVIEW" or level == "SENSITIVE" or score >= 50:
            return {"action": "ESCALATE_ADMIN", "reason": "Niveau Sensible ou revue manuelle recommandée.", "rules_applied": rules + ["review_needed"]}
        
        if action_rec == "AUTO_APPROVE":
             return {"action": "AUTO_APPROVE", "reason": "Niveau BASE avec tous les indicateurs au vert.", "rules_applied": rules + ["auto_clean"]}

        return {"action": "ESCALATE_ADMIN", "reason": "Décision par défaut (Prudence).", "rules_applied": rules + ["default_fallback"]}

    def _get_details(self, ticket) -> dict:
        details = ticket.requested_access_details or {}
        if isinstance(details, list): return details[0] if details else {}
        return details if isinstance(details, dict) else {}

    def _extract_environment(self, ticket) -> str:
        envs = ticket.requested_environments or []
        if not envs: return "DEV2"
        env = envs[0].upper() if isinstance(envs, list) else str(envs).upper()
        mapping = {"PRD": "PRD", "PROD": "PRD", "UAT": "UAT", "CRT": "CRT", "INV": "INV", "QL2": "QL2"}
        for k, v in mapping.items():
            if k in env: return v
        return "DEV2"

    def _extract_role(self, ticket) -> str:
        r = str(ticket.role or "").upper()
        if "STAGIAIRE" in r: return "STAGIAIRE"
        if "TRADER" in r: return "FRONT_OFFICE_TRADER"
        if "CHEF" in r or "MANAGER" in r: return "CHEF_DE_PROJET"
        return "DEVELOPPEUR"

    def _extract_application(self, ticket) -> str:
        d = self._get_details(ticket)
        app = d.get("application", "").upper()
        for a in ["T24", "MUREX", "SWIFT", "AML_TIDE", "E_BANKING"]:
            if a in app: return a
        return "E_BANKING"

    def _extract_access_type(self, ticket) -> str:
        d = self._get_details(ticket)
        acc = str(d.get("access_types", ["READ"])[0]).upper()
        if "DBA" in acc: return "DBA_ACCESS"
        if "DELETE" in acc: return "DELETE"
        if "ADMIN" in acc or "FULL" in acc: return "FULL_ACCESS"
        if "WRITE" in acc or "MODIF" in acc: return "WRITE"
        return "READ"

    def _extract_resource(self, ticket) -> str:
        d = self._get_details(ticket)
        res = d.get("resource", "").upper()
        if "TR" in res or "MONEY" in res: return "TRANSACTIONS_FINANCIERES"
        if "CLIENT" in res or "SENSITIVE" in res: return "DONNEES_CLIENTS_SENSIBLES"
        if "RH" in res: return "DONNEES_CARRIERES_RH"
        return "OTHER"

ai_service = AIService()