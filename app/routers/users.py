from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import models
from schemas import schemas
from routers.auth import get_current_user
from core import security
from services.audit_service import log_action, AuditLogAction

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_user)])

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if user_update.first_name:
        current_user.first_name = user_update.first_name
    if user_update.last_name:
        current_user.last_name = user_update.last_name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    log_action(db, action=AuditLogAction.USER_UPDATED, actor=current_user)
    return current_user