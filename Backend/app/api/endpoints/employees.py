# app/api/endpoints/employees.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.employee import Employee

router = APIRouter(prefix="/employees", tags=["Employés"])


@router.get("")
async def list_employees(
    team:     str = Query(None),
    seniority:str = Query(None),
    skip:     int = Query(0, ge=0),
    limit:    int = Query(100, ge=1, le=500),
    db:       Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Liste les employés avec filtres optionnels (équipe, séniorité)."""
    q = db.query(Employee)
    if team:
        q = q.filter(Employee.team == team)
    if seniority:
        q = q.filter(Employee.seniority == seniority)
    employees = q.offset(skip).limit(limit).all()
    return [
        {
            "id":       e.id,
            "name":     e.name,
            "email":    e.email,
            "team":     e.team,
            "role":     e.role,
            "seniority": e.seniority,
        }
        for e in employees
    ]


@router.get("/stats")
async def employee_stats(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user),
):
    """Statistiques sur les employés : répartition junior/senior par équipe."""
    total   = db.query(Employee).count()
    juniors = db.query(Employee).filter(Employee.seniority == "junior").count()
    seniors = db.query(Employee).filter(Employee.seniority == "senior").count()

    by_team = (
        db.query(Employee.team, Employee.seniority, func.count(Employee.id))
        .group_by(Employee.team, Employee.seniority)
        .all()
    )
    team_stats: dict = {}
    for team, seniority, count in by_team:
        if team not in team_stats:
            team_stats[team] = {"junior": 0, "senior": 0, "total": 0}
        team_stats[team][seniority or "junior"] = count
        team_stats[team]["total"] += count

    return {
        "total":    total,
        "juniors":  juniors,
        "seniors":  seniors,
        "by_team":  team_stats,
    }
