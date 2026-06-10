# app/api/endpoints/employee_portal.py
"""
Portail Employé — Endpoints publics (sans auth admin)
======================================================
Permet à un employé de soumettre une demande d'habilitation directement
depuis l'interface /employee du frontend.

Le timestamp de soumission = datetime.now() → timestamp réel utilisé
par le Modèle 2 pour la détection d'anomalies comportementales.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.employee import Employee
from app.models.ticket import Ticket, TicketStatus
from app.services.ai_service import ai_service

router = APIRouter(prefix="/portal", tags=["Portail Employé"])


# ─── Schéma de soumission employé ────────────────────────────────────────────

class EmployeeTicketRequest(BaseModel):
    employee_id:         str
    application:         str
    environment:         str
    access_type:         str
    resource:            str
    request_reason:      str
    justification:       Optional[str] = ""
    manager_approval:    Optional[str] = "none"


class EmployeeTicketResponse(BaseModel):
    ref:             str
    message:         str
    submitted_at:    str
    is_anomalous:    bool
    anomaly_severity: str
    ai_level:        str
    employee_name:   str


# ─── GET /portal/employees — Liste des employés pour le dropdown ─────────────

@router.get("/employees")
def get_employees_list(db: Session = Depends(get_db)):
    """
    Retourne la liste de tous les employés pour le dropdown de sélection.
    Endpoint public (pas d'auth requise) — lecture seule.
    """
    employees = db.query(Employee).order_by(Employee.name).all()
    return [
        {
            "id":       emp.id,
            "name":     emp.name,
            "email":    emp.email,
            "team":     emp.team,
            "role":     emp.role,
            "seniority": emp.seniority,
            "trust_score": emp.trust_score,
        }
        for emp in employees
    ]


# ─── POST /portal/submit — Soumettre une demande ────────────────────────────

@router.post("/submit", response_model=EmployeeTicketResponse)
def submit_employee_request(
    body: EmployeeTicketRequest,
    db: Session = Depends(get_db)
):
    """
    Crée un ticket de demande d'habilitation au nom d'un employé.

    - source = "EMPLOYEE_PORTAL"
    - employee_submitted_at = datetime.now() (timestamp réel de soumission)
    - Le Modèle 2 analysera ce timestamp pour détecter les anomalies
      (soumission le weekend, hors horaires, volume excessif, etc.)
    """
    # ── Vérifier que l'employé existe ────────────────────────────────────────
    employee = db.query(Employee).filter(Employee.id == body.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employé '{body.employee_id}' introuvable")

    # ── Timestamp RÉEL de soumission ─────────────────────────────────────────
    submitted_at = datetime.now()

    # ── Créer le ticket ──────────────────────────────────────────────────────
    ref = f"EMP-{submitted_at.strftime('%Y%m%d%H%M%S')}-{body.employee_id[-4:]}"

    ticket = Ticket(
        ref                     = ref,
        status                  = TicketStatus.NEW,
        employee_id             = employee.id,
        employee_name           = employee.name,
        employee_email          = employee.email,
        team_name               = employee.team,
        role                    = employee.role,
        description             = (
            f"[Portail Employé] {employee.name} ({employee.team}/{employee.role}) "
            f"demande un accès [{body.access_type}] sur [{body.application}] "
            f"en environnement [{body.environment}] — Motif: {body.request_reason}"
        ),
        requested_environments  = [body.environment],
        requested_access_details = {
            "access_types":             [body.access_type],
            "application":              body.application,
            "resource":                 body.resource,
            "user_seniority":           employee.seniority or "junior",
            "request_reason":           body.request_reason,
            "manager_approval_status":  body.manager_approval,
            "justification":            body.justification,
        },
        # ── Modèle 2 : Source réelle + timestamp de soumission employé ───────
        source                  = "EMPLOYEE_PORTAL",
        employee_submitted_at   = submitted_at,
    )

    db.add(ticket)
    db.flush()   # Obtenir l'ID sans commit

    # ── Classification IA + Détection Anomalie + Fusion ───────────────────────
    try:
        ai_result = ai_service.classify_and_save(db, ticket)
        final_level      = ai_result["classification"].get("level", "BASE")
        anomaly_severity = "NONE"
        is_anomalous     = False

        # Lire les résultats anomalie depuis la table anomaly_logs
        from app.models.anomaly_log import AnomalyLog
        alog = db.query(AnomalyLog).filter(
            AnomalyLog.ticket_id == ticket.id
        ).order_by(AnomalyLog.analyzed_at.desc()).first()

        if alog:
            anomaly_severity = alog.severity
            is_anomalous     = alog.is_anomalous

    except Exception as e:
        print(f"⚠️ [PORTAL] Erreur classification pour {ref}: {e}")
        final_level      = "BASE"
        anomaly_severity = "NONE"
        is_anomalous     = False
        db.commit()

    return EmployeeTicketResponse(
        ref              = ref,
        message          = f"Votre demande {ref} a été soumise et analysée par l'IA.",
        submitted_at     = submitted_at.isoformat(),
        is_anomalous     = is_anomalous,
        anomaly_severity = anomaly_severity,
        ai_level         = final_level,
        employee_name    = employee.name,
    )


# ─── GET /portal/options — Liste des choix possibles ─────────────────────────

@router.get("/options")
def get_portal_options(db: Session = Depends(get_db)):
    """
    Retourne les options possibles pour le formulaire (applications, envs, etc.)
    Ceci permet au frontend d'être dynamique et cohérent.
    """
    from app.models.systeme import Systeme
    systemes = db.query(Systeme).filter(Systeme.actif == True).all()
    
    # On structure par système pour que le frontend puisse filtrer
    systems_meta = []
    for s in systemes:
        systems_meta.append({
            "id": s.id,
            "nom": s.nom,
            "code": s.code,
            "apps": s.applications or [],
            "envs": s.environments or [],
            "sensibilite": s.sensibilite
        })
            
    # Fallback/Global lists for backward compatibility or simple selects
    apps = set()
    envs = set()
    for s in systemes:
        if s.applications:
            for app in s.applications: apps.add(app)
        if s.environments:
            for env in s.environments: envs.add(env)
    
    if not apps: apps = {"T24", "CRM_SIEBEL", "MUREX", "SWIFT", "E_BANKING", "AML_TIDE"}
    if not envs: envs = {"PRD", "UAT", "DEV", "TEST", "PREPROD"}
    
    return {
        "systems": systems_meta,
        "applications": sorted(list(apps)),
        "environments": sorted(list(envs)),
        "access_types": ["READ", "WRITE", "EXECUTE", "DELETE", "ADMIN"],
        "reasons": [
            {"id": "incident_production_bloquant", "label": "Incident Prod Bloquant"},
            {"id": "deploiement_version", "label": "Déploiement Version"},
            {"id": "demande_metier_urgente", "label": "Demande Métier Urgente"},
            {"id": "maintenance_preventive", "label": "Maintenance Préventive"},
            {"id": "audit_conformite", "label": "Audit / Conformité"},
            {"id": "test_performance", "label": "Test de Performance"}
        ],
        "resources": ["TRANSACTIONS_FINANCIERES", "CLIENT_DATA", "CONFIGURATION", "LOGS", "DATABASE", "OTHER"]
    }


# ─── GET /portal/status/{ref} — Consulter le statut d'une demande ───────────

@router.get("/status/{ref}")
def get_ticket_status(ref: str, db: Session = Depends(get_db)):
    """Permet à l'employé de consulter le statut de sa demande."""
    ticket = db.query(Ticket).filter(Ticket.ref == ref).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Demande '{ref}' introuvable")

    return {
        "ref":        ticket.ref,
        "status":     ticket.status.value,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "ai_level":   ticket.ai_level,
        "assigned_to": ticket.assigned_to,
    }
