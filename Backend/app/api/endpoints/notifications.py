# app/api/endpoints/notifications.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DashboardUser
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
async def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Récupère les notifications selon le rôle
    """
    if current_user.role == "SUPER_ADMIN":
        target_role = "SUPER_ADMIN"
    else:
        target_role = "ADMIN"
        
    # Notifications destinées à ce rôle
    # On regarde si le rôle de l'utilisateur est contenu dans target_roles
    notifications = db.query(Notification).filter(
        Notification.target_roles.contains(target_role)
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    result = []
    user_id_str = str(current_user.id)
    
    for n in notifications:
        # read_by est une liste JSON
        read_list = n.read_by or []
        is_read = user_id_str in read_list
        
        result.append({
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "timestamp": n.created_at.isoformat() if n.created_at else None,
            "read": is_read
        })
        
    return result

@router.put("/{notif_id}/read")
async def mark_as_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Marque une notification comme lue
    """
    notification = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
        
    user_id_str = str(current_user.id)
    read_list = notification.read_by or []
    
    if user_id_str not in read_list:
        new_read_list = read_list.copy()
        new_read_list.append(user_id_str)
        # SQLAlchemy and JSON sometimes require flag_modified or re-assignment
        notification.read_by = new_read_list
        db.commit()
        
    return {"status": "success"}

@router.put("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: DashboardUser = Depends(get_current_user)
):
    """
    Marque toutes les notifications affichées comme lues
    """
    if current_user.role == "SUPER_ADMIN":
        target_role = "SUPER_ADMIN"
    else:
        target_role = "ADMIN"
        
    notifications = db.query(Notification).filter(
        Notification.target_roles.contains(target_role)
    ).all()
    
    user_id_str = str(current_user.id)
    changed = False
    
    for n in notifications:
        read_list = n.read_by or []
        if user_id_str not in read_list:
            new_read_list = read_list.copy()
            new_read_list.append(user_id_str)
            n.read_by = new_read_list
            changed = True
            
    if changed:
        db.commit()
    return {"status": "success"}
