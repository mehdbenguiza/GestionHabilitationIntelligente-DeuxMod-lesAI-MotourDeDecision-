# app/services/ai_service.py

import joblib
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.feature_extractor import FeatureExtractor
from app.models.classification_result import ClassificationResult
from app.models.decision_engine import DecisionEngine
from app.models.ticket import Ticket, TicketStatus

class AIService:
    def __init__(self):
        self.model = None
        self.extractor = None
        self.is_loaded = False
        self.model_version = "1.0.0"
    
    def load_models(self):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            extractor_path = os.path.join(base_dir, "models", "feature_extractor.pkl")
            print(f"📂 Chargement extracteur depuis: {extractor_path}")
            self.extractor = FeatureExtractor()
            self.extractor.load(extractor_path)
            
            model_path = os.path.join(base_dir, "models", "classifier_model.pkl")
            print(f"📂 Chargement modèle depuis: {model_path}")
            self.model = joblib.load(model_path)
            
            self.is_loaded = True
            print(f"✅ Modèles IA chargés avec succès")
            print(f"   Classes disponibles: {self.model.classes_}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return False
    
    def classify_ticket_data(self, ticket_data: dict) -> dict:
        """Classifie un ticket à partir d'un dictionnaire"""
        if not self.is_loaded:
            print("⚠️ Modèle non chargé, utilisation des valeurs par défaut")
            # Fallback basé sur la criticité
            criticite = ticket_data.get('criticite', 'BASE')
            if criticite == 'CRITIQUE':
                return {
                    "level": "CRITICAL",
                    "confidence": 85.0,
                    "probabilities": {"BASE": 5.0, "SENSITIVE": 10.0, "CRITICAL": 85.0}
                }
            elif criticite == 'SENSIBLE':
                return {
                    "level": "SENSITIVE",
                    "confidence": 80.0,
                    "probabilities": {"BASE": 10.0, "SENSITIVE": 80.0, "CRITICAL": 10.0}
                }
            else:
                return {
                    "level": "BASE",
                    "confidence": 92.0,
                    "probabilities": {"BASE": 92.0, "SENSITIVE": 5.0, "CRITICAL": 3.0}
                }
        
        try:
            print(f"🔍 Ticket data reçu: {ticket_data}")
            
            features_df = self.extractor.transform_single_ticket(ticket_data)
            print(f"📊 Features extraites: {features_df.iloc[0].tolist()}")
            
            prediction = self.model.predict(features_df)[0]
            probabilities = self.model.predict_proba(features_df)[0]
            confidence = max(probabilities) * 100
            
            print(f"🤖 IA Prediction: {prediction} (confiance: {confidence:.2f}%)")
            print(f"   Probabilités: BASE={probabilities[self.model.classes_.tolist().index('BASE')]*100:.1f}%, "
                  f"SENSITIVE={probabilities[self.model.classes_.tolist().index('SENSITIVE')]*100:.1f}%, "
                  f"CRITICAL={probabilities[self.model.classes_.tolist().index('CRITICAL')]*100:.1f}%")
            
            return {
                "level": prediction,
                "confidence": round(confidence, 2),
                "probabilities": {
                    "BASE": round(probabilities[self.model.classes_.tolist().index('BASE')] * 100, 2),
                    "SENSITIVE": round(probabilities[self.model.classes_.tolist().index('SENSITIVE')] * 100, 2),
                    "CRITICAL": round(probabilities[self.model.classes_.tolist().index('CRITICAL')] * 100, 2)
                }
            }
        except Exception as e:
            print(f"❌ Erreur lors de la classification: {e}")
            import traceback
            traceback.print_exc()
            return {
                "level": "BASE",
                "confidence": 50.0,
                "probabilities": {"BASE": 50.0, "SENSITIVE": 25.0, "CRITICAL": 25.0}
            }
    
    def classify_ticket_model(self, ticket: Ticket) -> dict:
        """Classifie un ticket à partir d'un objet Ticket SQLAlchemy"""
        # Récupérer la criticité pour le fallback
        criticite = "BASE"
        details = ticket.requested_access_details or {}
        if details.get("criticite"):
            criticite = details.get("criticite")
        
        ticket_data = {
            "team": ticket.team_name or "MOE",
            "role": self._extract_role(ticket),
            "application": "MXP",
            "environment": self._extract_environment(ticket),
            "access_type": self._extract_access_type(ticket),
            "resource": self._extract_resource(ticket),
            "hour": ticket.created_at.hour if ticket.created_at else datetime.now().hour,
            "day_of_week": ticket.created_at.weekday() if ticket.created_at else datetime.now().weekday(),
            "criticite": criticite  # Pour le fallback
        }
        
        print(f"🔍 Données extraites pour IA: {ticket_data}")
        return self.classify_ticket_data(ticket_data)
    
    def _extract_environment(self, ticket) -> str:
        envs = ticket.requested_environments or []
        if envs:
            env = envs[0].upper().strip()
            # Nettoyer les préfixes connus
            for prefix in ["T24_", "ENV_"]:
                if env.startswith(prefix):
                    env = env[len(prefix):]
                    break
            # Mapping vers les valeurs connues du modèle
            mapping = {
                "DEV2": "DEV2",
                "DVR": "DVR",
                "QL2": "QL2",
                "CRT": "CRT",
                "INV": "INV",
                "PRD": "PRD",
                # Aliases courants
                "DEV": "DEV2",
                "PROD": "PRD",
                "PRODUCTION": "PRD",
                "QUALIF": "QL2",
                "RECETTE": "CRT",
            }
            return mapping.get(env, "DEV2")
        return "DEV2"
    
    def _extract_role(self, ticket) -> str:
        role_raw = ""
        if ticket.role:
            role_raw = str(ticket.role).upper()
            
        role_mapping = {
            "DEVELOPPEUR": "DEVELOPPEUR", "DEV": "DEVELOPPEUR", "DEVELOPER": "DEVELOPPEUR",
            "TECH_LEAD": "TECH_LEAD", "LEAD": "TECH_LEAD",
            "CHEF DE PROJET": "CHEF_DE_PROJET", "CHEF_DE_PROJET": "CHEF_DE_PROJET", "MANAGER": "CHEF_DE_PROJET",
            "STAGIAIRE": "STAGIAIRE", "INTERN": "STAGIAIRE",
            "BUSINESS_ANALYST": "BUSINESS_ANALYST", "BA": "BUSINESS_ANALYST", "PRODUCT_OWNER": "PRODUCT_OWNER", "PO": "PRODUCT_OWNER",
            "INGENIEUR_RESEAU": "INGENIEUR_RESEAU", "ADMINISTRATEUR": "ADMINISTRATEUR", "ADMIN": "ADMINISTRATEUR",
            "ANALYSTE_SOC": "ANALYSTE_SOC", "SOC": "ANALYSTE_SOC", "RSSI": "RSSI", "PENTESTER": "PENTESTER",
            "TESTEUR_QA": "TESTEUR_QA", "QA": "TESTEUR_QA", "TESTEUR": "TESTEUR_QA", "TEST_LEAD": "TEST_LEAD", "AUTOMATICIEN": "AUTOMATICIEN",
            "DATA_SCIENTIST": "DATA_SCIENTIST", "DATA_ENGINEER": "DATA_ENGINEER", "DATA_ANALYST": "DATA_ANALYST",
            "INTEGRATEUR": "INTEGRATEUR", "DEVELOPPEUR_MXP": "DEVELOPPEUR_MXP"
        }
        
        for k, v in role_mapping.items():
            if k in role_raw:
                return v
        return "DEVELOPPEUR" # Default neutral role
    def _extract_access_type(self, ticket) -> str:
        details = ticket.requested_access_details or {}
        access_types = details.get("access_types", [])
        if access_types:
            atype = access_types[0].upper()
            mapping = {
                "LECTURE": "READ", "ECRITURE": "WRITE",
                "EXECUTION": "EXECUTE", "ADMIN": "FULL_ACCESS",
                "SUPPRESSION": "DELETE", "MODIFICATION": "UPDATE",
                "777": "FULL_ACCESS",
                "SUPER ADMIN": "FULL_ACCESS",
                "SUPER_ADMIN": "FULL_ACCESS",
                "DELETE": "DELETE",
                "UPDATE": "UPDATE"
            }
            # Chercher la correspondance
            for fr, en in mapping.items():
                if fr in atype:
                    return en
            return "READ"
        return "READ"
    
    def _extract_resource(self, ticket) -> str:
        details = ticket.requested_access_details or {}
        criticite = details.get("criticite", "BASE")
        if criticite == "CRITIQUE":
            return "PRODUCTION"
        elif criticite == "SENSIBLE":
            return "PERSONAL_DATA"
        return "OTHER"
    
    def classify_and_save(self, db: Session, ticket: Ticket) -> dict:
        """Classifie un ticket, sauvegarde le résultat et retourne la décision"""
        print(f"🔍 classify_and_save appelé pour ticket #{ticket.id}")
        
        result = self.classify_ticket_model(ticket)
        print(f"📊 Résultat classification: {result['level']} (confiance: {result['confidence']}%)")
        
        classification = ClassificationResult(
            ticket_id=ticket.id,
            predicted_level=result['level'],
            confidence=result['confidence'],
            probabilities=result['probabilities'],
            model_version=self.model_version,
            processed_at=datetime.utcnow()
        )
        db.add(classification)
        db.flush()
        
        decision = self._apply_decision_rules(result)
        
        decision_record = DecisionEngine(
            ticket_id=ticket.id,
            classification_id=classification.id,
            final_level=result['level'],
            final_confidence=result['confidence'],
            recommended_action=decision['action'],
            action_reason=decision['reason'],
            rules_applied=decision['rules_applied'],
            processed_at=datetime.utcnow()
        )
        db.add(decision_record)
        
        # Logique d'assignation
        from app.models.notification import Notification
        
        if decision['action'] == 'AUTO_APPROVE':
            ticket.status = TicketStatus.APPROVED
            ticket.assigned_to = None
        elif decision['action'] == 'ESCALATE_ADMIN':
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = 'ADMIN,SUPER_ADMIN'
        else:
            # ESCALATE_SUPER_ADMIN
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = 'SUPER_ADMIN'
            
            # Créer une notification pour les Super Admins
            notif = Notification(
                title=f"Ticket CRITIQUE reçu : {ticket.ref}",
                message=f"L'IA a détecté une demande critique (Confiance: {result['confidence']}%). Équipe: {ticket.team_name}.",
                type="danger",
                target_roles="SUPER_ADMIN"
            )
            db.add(notif)
        
        ticket.assigned_at = datetime.utcnow()
        db.commit()
        
        return {
            "classification": result,
            "decision": decision,
            "ticket_updated": {
                "status": ticket.status.value,
                "assigned_to": ticket.assigned_to
            }
        }
    
    def _apply_decision_rules(self, classification_result: dict) -> dict:
        level = classification_result['level']
        confidence = classification_result['confidence']
        rules_applied = []
        
        if level == 'CRITICAL':
            action = 'ESCALATE_SUPER_ADMIN'
            reason = f"Niveau CRITIQUE (confiance: {confidence}%) - Escalade Super Admin obligatoire"
            rules_applied.append("critical_level_rule")
        elif level == 'SENSITIVE':
            action = 'ESCALATE_ADMIN'
            reason = f"Niveau SENSITIVE (confiance: {confidence}%) - Validation Admin requise"
            rules_applied.append("sensitive_level_rule")
        else:
            if confidence >= 70:
                action = 'AUTO_APPROVE'
                reason = f"Niveau BASE avec confiance élevée ({confidence}%) - Auto-approbation"
                rules_applied.append("base_high_confidence_rule")
            else:
                action = 'ESCALATE_ADMIN'
                reason = f"Niveau BASE mais confiance faible ({confidence}%) - Escalade Admin par précaution"
                rules_applied.append("base_low_confidence_rule")
        
        return {"action": action, "reason": reason, "rules_applied": rules_applied}


ai_service = AIService()