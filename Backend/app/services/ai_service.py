# app/services/ai_service.py

import joblib
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.feature_extractor import FeatureExtractor
from app.models.classification_result import ClassificationResult
from app.models.decision_engine import DecisionEngine
from app.models.ticket import Ticket, TicketStatus
from app.models.automation_rule import AutomationRule
from app.services.audit_service import audit_service
from app.services.nlp_service import nlp_service
from app.services.trust_score_service import trust_score_service
from app.services.anomaly_service import anomaly_service
from app.services.decision_fusion_service import decision_fusion_service

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
    risk_label = RISK_LABEL_VERBOSE.get(level, "Niveau indtermin")
    total_score = sum([v[0] for v in factors.values()])
    
    # Requirement 3: Tri par importance (valeur absolue des points)
    sorted_items = sorted(
        factors.items(),
        key=lambda x: abs(x[1][0]),
        reverse=True
    )

    # Requirement 8 & 10 (v2.0): Niveaux de confiance pro
    if confidence < 0.60:
        confidence_note = "[NOTE] Note : Faible confiance - décision incertaine (analyse ML divergente)"
    elif confidence < 0.80:
        confidence_note = "[OK] Note : Confiance modérée"
    else:
        confidence_note = "[FAST] Note : Décision fiable (forte cohérence IA/Métier)"

    lines = []
    # Afficher les 4 plus gros facteurs
    for _, (pts, desc) in sorted_items[:4]:
        sign = "+" if pts >= 0 else ""
        lines.append(f"• {desc} ({sign}{pts} pts)")

    suffix = ""
    if source == "human_correction":
        suffix = "\n[!] Classification imposée par la bibliothèque d'expertise humaine."

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
        self.label_encoder = None
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
            
            le_path = os.path.join(models_dir, "label_encoder.pkl")
            if os.path.exists(le_path):
                self.label_encoder = joblib.load(le_path)
            else:
                self.label_encoder = None

            self.is_loaded = True
            print(f"INFO: Modeles IA v{self.model_version} charges avec succes")

            # ── Modèle 2 : Charger l'Isolation Forest ────────────────────────
            anomaly_service.load_model()

            # ── Moteur de Décision NN : Charger ou pré-entraîner le MLP ──────
            from app.services.nn_fusion_engine import nn_fusion_engine
            nn_fusion_engine.load_or_init()
            # ─────────────────────────────────────────────────────────────────

            return True
        except Exception as e:
            print(f"ERROR: chec chargement IA : {e}")
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
                correction.last_used_at = datetime.now(timezone.utc)
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
                "confidence_level": "[OK] Confiance modérée (Règles métier)",
                "explanation": _build_explanation(rule_level, factors, 0.7, source="fallback"),
                "details": factors,
                "triggered_rules": [f"{desc} ({pts} pts)" for _, (pts, desc) in factors.items()],
                "decision_source": "RULES_ONLY (Fallback)",
                "consistency": {"status": "OK", "message": "Mode dgrad active"},
                "recommended_action": "MANUAL_REVIEW" if rule_level != "BASE" else "AUTO_APPROVE",
                "source": "fallback",
             }

        try:
            features_df  = self.extractor.transform_single_ticket(ticket_data)
            prediction_raw   = self.model.predict(features_df)[0]
            probabilities= self.model.predict_proba(features_df)[0]
            confidence   = float(round(max(probabilities) * 100, 2))

            classes   = self.model.classes_.tolist()
            
            # Gérer le LabelEncoder pour XGBoost
            if self.label_encoder is not None:
                prediction = self.label_encoder.inverse_transform([prediction_raw])[0]
                classes_str = self.label_encoder.inverse_transform(classes).tolist()
            else:
                prediction = prediction_raw
                classes_str = classes

            prob_dict = {
                "BASE":      float(round(probabilities[classes_str.index("BASE")] * 100, 2)),
                "SENSITIVE": float(round(probabilities[classes_str.index("SENSITIVE")] * 100, 2)),
                "CRITICAL":  float(round(probabilities[classes_str.index("CRITICAL")] * 100, 2)),
            }

            # Requirement 1 (v2.0): Vérifier cohérence
            consistency = "OK"
            consistency_msg = "ML et règles métiers alignés"
            if prediction != rule_level:
                consistency = "WARNING"
                consistency_msg = f"Incohérence détectée : ML={prediction} vs RULES={rule_level}"

            # Requirement 4 & 10 (v2.0): Confidence nuance
            if confidence < 50:
                warning_label = " Trs faible confiance IA"
            elif confidence < 70:
                warning_label = " Confiance modre"
            else:
                warning_label = "[OK] Confiance leve"

            classification_source = "model"

            # ── V3.0 : SHAP Values Explanation (XGBoost) ──
            shap_values_dict = {}
            try:
                import shap
                # Initialiser l'explainer sur l'arbre (très rapide pour XGB/RF)
                explainer = shap.TreeExplainer(self.model)
                shap_vals = explainer.shap_values(features_df)
                
                # shap_values pour classification multiclasses
                class_index = classes.index(prediction_raw)
                
                if isinstance(shap_vals, list):
                    # Random Forest
                    local_shap = shap_vals[class_index][0]
                elif len(shap_vals.shape) == 3:
                    # XGBoost
                    local_shap = shap_vals[0, :, class_index]
                else:
                    local_shap = shap_vals[0]
                    
                feature_names = features_df.columns.tolist()
                
                # Ziper et trier par valeur absolue
                shap_pairs = list(zip(feature_names, local_shap))
                shap_pairs.sort(key=lambda x: abs(x[1]), reverse=True)
                
                # Garder le top 5
                for f_name, s_val in shap_pairs[:5]:
                    if abs(s_val) > 0.001:  # Ignorer les bruits insignifiants
                        shap_values_dict[f_name] = round(float(s_val), 4)
                        
            except Exception as e:
                print(f"INFO: SHAP non calcul ({e})")
            
            # ─────────────────────────────────────────────

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
                "shap_values":  shap_values_dict,
                "source":       "model",
            }
        except Exception as e:
            print(f"ERROR classification: {e}")
            return { "level": "BASE", "risk_level": "BASE", "risk_score": 0, "confidence": 50.0, "probabilities": {}, "explanation": "Erreur technique IA.", "source": "error", "details": {}, "shap_values": {} }

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

        # [OK] Lire la séniorité RÉELLE depuis la table employees
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

        # ── V3.0 : Appels aux nouveaux services (NLP + Trust Score) ──────────
        
        # 1. Analyse Sémantique NLP de la justification
        justification_text = details.get("justification", "")
        nlp_res = nlp_service.analyze_justification(
            justification=justification_text,
            request_reason=ticket_data["request_reason"],
            role=ticket_data["role"],
            environment=ticket_data["environment"]
        )
        nlp_modifier = nlp_service.score_to_risk_modifier(nlp_res["nlp_score"])

        # 2. Récupération Trust Score employé
        trust_res = {}
        trust_modifier = 0
        if ticket.employee_id and db is not None:
             trust_res = trust_score_service.compute_trust_score(ticket.employee_id, db)
             trust_modifier = trust_res.get("risk_modifier", 0)

        # 3. Application des RÈGLES D'AUTOMATISATION DYNAMIQUES (Supervision)
        dynamic_factors = {}
        if db is not None:
            try:
                active_rules = db.query(AutomationRule).filter(
                    AutomationRule.equipe == ticket_data["team"],
                    AutomationRule.actif == True
                ).all()
                
                for rule in active_rules:
                    # Vérifier si le rôle et l'environnement correspondent
                    role_match = not rule.roles or any(r.upper() in ticket_data["role"].upper() for r in rule.roles)
                    env_match = not rule.environnements or any(e.upper() == ticket_data["environment"].upper() for e in rule.environnements)
                    
                    if role_match and env_match:
                        # Vérifier si l'accès demandé est dans les accès par défaut
                        for acc in rule.acces_par_defaut:
                            if acc["nom"].upper() in ticket_data["access_type"].upper():
                                # Match ! On réduit le risque car c'est une règle pré-approuvée
                                bonus = -30 if acc["niveau"] == "Base" else -15
                                dynamic_factors["dynamic_rule_" + str(rule.id)] = (bonus, f"Règle d'automatisation : {rule.equipe} - {acc['nom']}")
            except Exception as e:
                print(f"WARNING: Erreur lors de l'application des regles dynamiques: {e}")

        # ─────────────────────────────────────────────────────────────────────

        if db is not None:
            correction = self.check_corrections(db, ticket_data)
            # Si correction experte, on injecte quand-même les stats NLP/Trust
            if correction:
                 correction.update({
                      "nlp_score": nlp_res["nlp_score"],
                      "nlp_label": nlp_res["nlp_label"],
                      "trust_score": trust_res.get("trust_score"),
                      "trust_label": trust_res.get("trust_label"),
                      "trust_modifier": trust_modifier,
                 })
                 return correction

        # Classification de base
        result = self.classify_ticket_data(ticket_data)

        # ── V3.0 : Application des modificateurs de score et enrichissement ──
        base_score = result["risk_score_rules"]
        
        # Ajouter les facteurs dynamiques
        for k, v in dynamic_factors.items():
            result["details"][k] = v
            base_score += v[0]
            
        final_score = base_score + nlp_modifier + trust_modifier
        final_score = max(0, min(200, final_score)) # Clamp
        
        result["risk_score_rules"] = final_score
        result["risk_score"]       = final_score

        # Mise à jour du niveau heuristique si le modificateur le fait basculer
        if final_score >= 85 and result["rule_based_level"] != "CRITICAL":
            result["rule_based_level"] = "CRITICAL"
            result["consistency"]["status"] = "WARNING" if result["prediction"] != "CRITICAL" else "OK"
        elif final_score >= 50 and result["rule_based_level"] == "BASE":
            result["rule_based_level"] = "SENSITIVE"
            result["consistency"]["status"] = "WARNING" if result["prediction"] != "SENSITIVE" else "OK"

        # Injection des stats dans le résultat final pour l'enregistrement
        result["nlp_score"]      = nlp_res["nlp_score"]
        result["nlp_label"]      = nlp_res["nlp_label"]
        result["trust_score"]    = trust_res.get("trust_score")
        result["trust_label"]    = trust_res.get("trust_label")
        result["trust_modifier"] = trust_modifier
        
        # Ajout à l'explication visuelle
        if nlp_modifier != 0:
             result["details"]["nlp_ana"] = (nlp_modifier, f"[NLP V3] Analyse smantique : {nlp_res['nlp_label']} ({nlp_res['nlp_score']}/100)")
        if trust_modifier != 0:
             result["details"]["trust_ana"] = (trust_modifier, f"[TRUST V3] Rputation employ : {trust_res.get('trust_label')} (Score: {trust_res.get('trust_score')})")

        # ── V3.0 : Injection SHAP dans l'explication UX si disponible ──
        if "shap_values" in result and result["shap_values"]:
             shap_txt = "\n\n[STATS] Poids des vecteurs M.L (SHAP) :\n"
             for feat, val in result["shap_values"].items():
                 shap_txt += f"  - {feat} : {val:+.2f}\n"
             result["explanation"] += shap_txt

        # Régénérer l'explication avec les nouveaux facteurs
        # ... (dj fait plus haut, on ajoute juste le texte SHAP ici  result["explanation"])
        
        return result

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
            
            # Nouveaux champs V3.0 (NLP & SHAP)
            nlp_score               = result.get("nlp_score"),
            nlp_label               = result.get("nlp_label"),
            trust_modifier          = result.get("trust_modifier"),
            shap_values             = result.get("shap_values"),

            processed_at            = datetime.now(timezone.utc),
        )
        db.add(classification)

        # ── MODÈLE 2 : Détection d'Anomalies Comportementales ───────────────
        anomaly_result = anomaly_service.analyze_ticket(ticket, db)

        # ── MOTEUR NN : Décision Finale (MLP Tri-Polaire) ───────────────────
        from app.services.nn_fusion_engine import nn_fusion_engine
        nn_pred = nn_fusion_engine.predict(result, anomaly_result)

        # Compatibilité avec le reste du code (ancien format fusion)
        fusion = {
            "final_level":       nn_pred["final_level"],
            "original_level":    result.get("level", "BASE"),
            "anomaly_severity":  nn_pred["anomaly_severity"],
            "anomaly_flags":     anomaly_result.get("flags", []),
            "is_anomalous":      anomaly_result.get("is_anomalous", False),
            "anomaly_overridden": nn_pred["final_level"] != result.get("level"),
            "final_risk_score":  min(200, result.get("risk_score_rules", 0) + nn_pred["risk_boost"]),
            "anomaly_score":     anomaly_result.get("anomaly_score"),
            "fusion_explanation": decision_fusion_service.fuse(result, anomaly_result)["fusion_explanation"],
            "risk_boost":        nn_pred["risk_boost"],
            # Champs spécifiques NN (pour audit)
            "nn_probabilities":  nn_pred.get("nn_probabilities", {}),
            "nn_confidence":     nn_pred.get("nn_confidence", 0.0),
            "fusion_mode":       nn_pred.get("fusion_mode", "RULE"),
        }

        # Appliquer le niveau final de la fusion
        final_level = fusion["final_level"]
        if final_level != classification.predicted_level:
            print(f"[FUSION] Override anomalie : {classification.predicted_level} -> {final_level} "
                  f"(anomalie severite: {fusion['anomaly_severity']})")
        classification.predicted_level = final_level
        classification.explanation = fusion["fusion_explanation"]
        
        # Ajouter les infos NN à l'explication et à la source (pour audit sans changer le schéma DB)
        classification.decision_source = f"HYBRID (M1 + M2 {fusion['fusion_mode']})"
        if fusion['fusion_mode'] == 'NN':
            nn_conf_pct = round(fusion['nn_confidence'] * 100, 1)
            classification.explanation += f"\n\n[NN] Fusion Tri-Polaire (Rseau de Neurones) : Confiance {nn_conf_pct}%"
            
        classification.risk_score_rules = fusion["final_risk_score"]
        
        # Injecter le boost anomalie dans les facteurs de risque pour affichage frontend
        # NOTE: Toujours re-assigner un nouveau dict pour que SQLAlchemy détecte la mutation JSON
        current_factors = dict(classification.risk_factors or {})
        if fusion["risk_boost"] > 0:
            current_factors["ANOMALY_BOOST"] = [fusion["risk_boost"], f"Anomalie comportementale ({fusion['anomaly_severity']})"]
        # Vérification de cohérence : sum(factors) doit égaler risk_score_rules
        factors_sum = sum(v[0] for v in current_factors.values())
        clamped_score = max(0, min(200, factors_sum))
        classification.risk_score_rules = clamped_score
        classification.risk_factors = current_factors
        
        # Mettre à jour les triggered_rules avec TOUS les modificateurs (NLP, Trust, Anomaly)
        classification.triggered_rules = [f"{desc} ({'+' if pts > 0 else ''}{pts} pts)" for _, (pts, desc) in current_factors.items()]
        # ─────────────────────────────────────────────────────────────────────

        # 🔔 ALERTE : Notification basée sur le niveau FINAL (après fusion)
        predicted = final_level
        if predicted == "CRITICAL":
            audit_service.notify(
                db=db,
                title=f"ALERTE: Ticket Critique {ticket.ref}",
                message=f"Risque lev dtect sur {ticket.ref} ({ticket.employee_name}). Validation immdiate requise."
                        + (f" [!] Anomalie comportementale : {fusion['anomaly_severity']}" if fusion["is_anomalous"] else ""),
                type="danger"
            )
        elif predicted == "SENSITIVE":
            audit_service.notify(
                db=db,
                title=f"Alerte: Ticket Sensible {ticket.ref}",
                message=f"Le ticket {ticket.ref} demande une revue d'accs."
                        + (f" [!] Anomalie : {', '.join(fusion['anomaly_flags'][:2])}" if fusion["is_anomalous"] else ""),
                type="warning"
            )
        else:
            audit_service.notify(
                db=db,
                title=f"Info: Nouveau Ticket {ticket.ref}",
                message=f"Ticket de niveau BASE auto-analys.",
                type="info"
            )
        print(f"[NOTIF] Notification creee pour le ticket {ticket.ref} ({predicted})"
              + (f" | Anomalie: {fusion['anomaly_severity']}" if fusion["is_anomalous"] else ""))

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
            processed_at       = datetime.now(timezone.utc),
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
                print(f"[!] [AUTO-APPROVE] Erreur lors de la cration du profil automatise pour {ticket.ref}: {e}")
            # ------------------------------------------------------------------
        elif decision["action"] == "ESCALATE_ADMIN":
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = "ADMIN"
        else:
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = "SUPER_ADMIN"

        ticket.assigned_at = datetime.now(timezone.utc)
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
                "reason": f"Alerte de cohrence: Dsaccord ML/Mtier ({result['consistency']['message']})",
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