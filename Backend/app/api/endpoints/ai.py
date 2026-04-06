# app/api/endpoints/ai.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai_service import ai_service   # ← Utiliser le singleton global, pas une nouvelle instance
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser

router = APIRouter(prefix="/ai", tags=["AI"])

# ✅ CORRECTION : On n'instancie PAS un nouveau AIService ici, on utilise le singleton
# L'ancien code créait une 2e instance et appelait load_models() une 2e fois inutilement


class TicketInput(BaseModel):
    """Modèle pour les données d'entrée du ticket"""
    team: str
    application: str
    environment: str
    access_type: str
    resource: str
    hour: Optional[int] = None
    day_of_week: Optional[int] = None


@router.post("/classify")
async def classify_ticket(
    ticket: TicketInput,
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Classifie un ticket et retourne le niveau d'accès prédit
    """
    try:
        # Convertir en dictionnaire
        ticket_dict = ticket.dict()

        # Ajouter des valeurs par défaut si manquantes
        if ticket_dict.get('hour') is None:
            ticket_dict['hour'] = datetime.now().hour
        if ticket_dict.get('day_of_week') is None:
            ticket_dict['day_of_week'] = datetime.now().weekday()

        # ✅ CORRECTION : La méthode correcte s'appelle classify_ticket_data (pas get_ai_recommendation)
        result = ai_service.classify_ticket_data(ticket_dict)

        return {
            "status": "success",
            "ticket": ticket_dict,
            "ai_analysis": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_health():
    """Vérifie si le modèle IA est chargé"""
    return {
        "status": "ready" if ai_service.is_loaded else "not_ready",
        "model_version": ai_service.model_version,
        "message": "Modèle IA chargé" if ai_service.is_loaded else "Modèle non chargé — mode fallback actif"
    }

@router.get("/metrics")
async def ai_metrics(db: Session = Depends(get_db)):
    """Récupère les statistiques d'IA groupées"""
    from app.models.classification_result import ClassificationResult
    from app.models.decision_engine import DecisionEngine
    from sqlalchemy import func
    
    total = db.query(ClassificationResult).count()
    if total == 0:
        return {"total": 0, "levels": {}, "auto_approve_rate": 0, "avg_confidence": 0, "daily_stats": []}
        
    # Niveaux
    levels = db.query(ClassificationResult.predicted_level, func.count(ClassificationResult.id)).group_by(ClassificationResult.predicted_level).all()
    levels_dict = {l[0]: l[1] for l in levels}
    
    # Auto approve
    auto_approve = db.query(DecisionEngine).filter(DecisionEngine.recommended_action == 'AUTO_APPROVE').count()
    auto_approve_rate = round((auto_approve / total) * 100, 2)
    
    # Avg confidence
    avg_conf = db.query(func.avg(ClassificationResult.confidence)).scalar() or 0
    avg_conf = round(avg_conf, 2)
    
    # Stats par jour (SQLite utilise date() pour formater, MySQL utilise DATE())
    # On va utiliser text() si besoin, ou simplement func.date() supporté par beaucoup de dialects
    try:
        from sqlalchemy import cast, Date
        daily = db.query(
            cast(ClassificationResult.processed_at, Date).label("date"),
            ClassificationResult.predicted_level,
            func.count(ClassificationResult.id).label("count")
        ).group_by(
            cast(ClassificationResult.processed_at, Date),
            ClassificationResult.predicted_level
        ).order_by(
            cast(ClassificationResult.processed_at, Date).desc()
        ).limit(30).all()
        
        daily_stats = []
        for d in daily:
            daily_stats.append({
                "date": d.date.isoformat() if d.date else None,
                "level": d.predicted_level,
                "count": d.count
            })
    except Exception as e:
        daily_stats = []
        print(e)
        
    return {
        "total": total,
        "levels": levels_dict,
        "auto_approve_rate": auto_approve_rate,
        "avg_confidence": avg_conf,
        "daily_stats": daily_stats
    }

@router.get("/decisions")
async def ai_decisions(db: Session = Depends(get_db)):
    """Récupère l'historique des décisions de l'IA (Anomalies)"""
    from app.models.decision_engine import DecisionEngine
    from app.models.ticket import Ticket
    
    # On prend les 100 dernières décisions
    decisions = db.query(DecisionEngine, Ticket).join(Ticket, DecisionEngine.ticket_id == Ticket.id).order_by(DecisionEngine.processed_at.desc()).limit(100).all()
    
    result = []
    for d, t in decisions:
        result.append({
            "id": d.id,
            "ticketRef": t.ref,
            "demandeur": t.employee_name or t.employee_id,
            "equipe": t.team_name,
            "demande": t.description,
            "niveauPredit": d.final_level,
            "niveauReel": d.final_level, # Simplification
            "scoreConfiance": round(d.final_confidence, 2),
            "anomalie": d.final_level == 'CRITICAL' or d.final_confidence < 60, # Simulation heuristique d'anomalie
            "reasoning": d.rules_applied or [d.action_reason],
            "date": d.processed_at.isoformat() if d.processed_at else None,
            "severity": 'critical' if d.final_level == 'CRITICAL' else 'high'
        })
        
    return result