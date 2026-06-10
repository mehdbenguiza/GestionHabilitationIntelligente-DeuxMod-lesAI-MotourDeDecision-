
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.automation_rule import AutomationRule
from pydantic import BaseModel

router = APIRouter(prefix="/automation-rules", tags=["Automation Rules"])

class RuleBase(BaseModel):
    equipe: str
    roles: List[str]
    environnements: List[str]
    acces_par_defaut: List[dict]

class RuleCreate(RuleBase):
    pass

@router.get("")
def list_rules(db: Session = Depends(get_db), current_user: DashboardUser = Depends(get_current_user)):
    rules = db.query(AutomationRule).all()
    return [
        {
            "id": str(r.id),
            "equipe": r.equipe,
            "roles": r.roles,
            "environnements": r.environnements,
            "accesParDefaut": r.acces_par_defaut
        }
        for r in rules
    ]

@router.post("")
def create_rule(rule: RuleCreate, db: Session = Depends(get_db), current_user: DashboardUser = Depends(get_current_user)):
    new_rule = AutomationRule(
        equipe=rule.equipe,
        roles=rule.roles,
        environnements=rule.environnements,
        acces_par_defaut=rule.acces_par_defaut
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return {"status": "success", "id": str(new_rule.id)}

@router.put("/{rule_id}")
def update_rule(rule_id: int, rule: RuleCreate, db: Session = Depends(get_db), current_user: DashboardUser = Depends(get_current_user)):
    db_rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    
    db_rule.equipe = rule.equipe
    db_rule.roles = rule.roles
    db_rule.environnements = rule.environnements
    db_rule.acces_par_defaut = rule.acces_par_defaut
    
    db.commit()
    return {"status": "success"}

@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db), current_user: DashboardUser = Depends(get_current_user)):
    db_rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    
    db.delete(db_rule)
    db.commit()
    return {"status": "success"}
