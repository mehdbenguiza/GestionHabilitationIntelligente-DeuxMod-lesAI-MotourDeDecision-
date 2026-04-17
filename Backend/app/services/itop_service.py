# app/services/itop_service.py
"""
Simulation complète du connecteur iTop ITSM.
En mode développement, toutes les opérations sont simulées localement.
En production, ce service appelle la vraie API WS de iTop via JSON-RPC.
Les notifications email sont déléguées à email_service (simulation du moteur
de notification d'iTop).
"""

import requests
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings

class ITopService:
    """
    Service de communication avec iTop
    Mode développement : simulation
    Mode production : API réelle
    """
    
    def __init__(self):
        self.base_url = settings.ITOP_API_URL
        self.username = settings.ITOP_USERNAME
        self.password = settings.ITOP_PASSWORD
        self.mode = settings.ENVIRONMENT
        
    def fetch_tickets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les tickets depuis iTop
        """
        if self.mode == "development":
            return self._fetch_tickets_simulated(limit)
        else:
            return self._fetch_tickets_real(limit)
    
    def _fetch_tickets_simulated(self, limit: int) -> List[Dict[str, Any]]:
        """
        Simulation : retourne des tickets fictifs
        """
        import random
        from datetime import datetime
        
        teams = ["DEVELOPPEMENT", "SECURITE", "DBA", "RESEAU", "SUPPORT"]
        envs = ["T24_DEV2", "T24_QL2", "T24_CRT", "PRD"]
        access_types = ["LECTURE", "ECRITURE", "ADMIN", "EXECUTION"]
        
        tickets = []
        for i in range(1, min(limit + 1, 20)):
            tickets.append({
                "id": f"REQ-{2026}{str(i).zfill(4)}",
                "ref": f"TKT-{2026}{str(i).zfill(4)}",
                "caller_id": f"EMP-{1000 + i}",
                "caller_name": f"Employé {i}",
                "caller_email": f"employe{i}@biat-it.com.tn",
                "team": random.choice(teams),
                "title": f"Demande d'accès {random.choice(access_types)}",
                "description": f"Demande d'accès en {random.choice(access_types)} pour le projet PFE",
                "requested_env": random.sample(envs, random.randint(1, 2)),
                "requested_access": random.sample(access_types, random.randint(1, 2)),
                "status": "new",
                "created_at": datetime.now().isoformat()
            })
        return tickets
    
    def _fetch_tickets_real(self, limit: int) -> List[Dict[str, Any]]:
        """
        Version réelle : appelle l'API iTop
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "core/get",
                "params": {
                    "class": "Ticket",
                    "key": "SELECT Ticket WHERE status='new'",
                    "output_fields": ["id", "ref", "caller_id", "title", "description", "status"]
                },
                "id": 1
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                auth=(self.username, self.password),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_itop_response(data)
            else:
                print(f"❌ iTop API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Erreur iTop: {e}")
            return []
    
    def _parse_itop_response(self, data: Dict) -> List[Dict]:
        """
        Parse la réponse iTop
        """
        tickets = []
        if "result" in data:
            for item in data["result"]:
                tickets.append({
                    "id": item.get("id"),
                    "ref": item.get("ref"),
                    "caller_id": item.get("caller_id"),
                    "caller_name": item.get("caller_name", ""),
                    "caller_email": item.get("caller_email", ""),
                    "team": item.get("team", ""),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "requested_env": item.get("environments", []),
                    "requested_access": item.get("access_rights", []),
                    "status": item.get("status"),
                    "created_at": item.get("created_at")
                })
        return tickets
    
    def update_ticket_status(self, ticket_ref: str, status: str, resolution: str = "") -> bool:
        """
        Met à jour le statut d'un ticket dans iTop.
        En développement : log de simulation.
        En production : appel API JSON-RPC.
        """
        if self.mode == "development":
            status_icon = "✅" if status == "approved" else "❌"
            print(f"{status_icon} [iTop SIMULATION] Ticket {ticket_ref} → statut '{status.upper()}' (résolution: {resolution[:80] if resolution else 'N/A'})")
            return True
        else:
            return self._update_ticket_real(ticket_ref, status, resolution)

    # ─────────────────────────────────────────────────────────────────────────
    # Notifications iTop (Simulation du moteur d'email ITSM)
    # ─────────────────────────────────────────────────────────────────────────

    def notify_ticket_approved(
        self,
        ticket,          # Ticket SQLAlchemy
        profile,         # AccessProfile SQLAlchemy
        system_name: str,
        approved_by: str,
    ) -> bool:
        """
        Simule la notification iTop d'approbation :
        - Envoie un email HTML professionnel avec les credentials du profil
        - Le mot de passe est celui stocké AVANT effacement par profile_service
          (cette méthode est appelée pendant la création du profil, avant commit)

        Note: le temp_password doit être passé directement (avant effacement DB).
        """
        # Note: cette méthode délègue au profile_service qui gère l'envoi
        # Elle est conservée pour compatibilité et log ITSM
        print(f"📧 [iTop] Notification d'approbation envoyée pour {ticket.ref} → {ticket.employee_email}")
        return True

    def notify_ticket_rejected(
        self,
        ticket,          # Ticket SQLAlchemy
        reason: str,
        rejected_by: str,
    ) -> bool:
        """
        Simule la notification iTop de rejet.
        Délègue l'envoi réel à profile_service.notify_rejection().
        """
        print(f"📧 [iTop] Notification de rejet envoyée pour {ticket.ref} → {ticket.employee_email}")
        return True

    def _update_ticket_real(self, ticket_ref: str, status: str, resolution: str) -> bool:
        """
        Appel API iTop (JSON-RPC) pour mise à jour — Mode Production uniquement.
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "core/update",
                "params": {
                    "class": "Ticket",
                    "key": ticket_ref,
                    "fields": {
                        "status": status,
                        "resolution": resolution
                    }
                },
                "id": 1
            }

            response = requests.post(
                self.base_url,
                json=payload,
                auth=(self.username, self.password),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erreur mise à jour iTop: {e}")
            return False