import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from models import models
from schemas import schemas
from routers.auth import get_current_user, get_user
from core import security
from services.audit_service import log_action, AuditLogAction

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    return current_user

router.dependencies.append(Depends(get_admin_user))

@router.get("/users", response_model=List[schemas.User])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id).all()

@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(user: schemas.UserCreate, db: Session = Depends(get_db), admin_user: models.User = Depends(get_admin_user)):
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=models.UserRole.USER
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log_action(db, action=AuditLogAction.USER_CREATED, actor=admin_user, details={"created_user_email": new_user.email})
    return new_user

@router.get("/users/{user_uuid}", response_model=schemas.User)
def get_user_details(user_uuid: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user

@router.put("/users/{user_uuid}/role", response_model=schemas.User)
def change_user_role(user_uuid: uuid.UUID, role: models.UserRole, db: Session = Depends(get_db), admin_user: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.role = role
    db.commit()
    db.refresh(user)
    log_action(db, action=AuditLogAction.USER_ROLE_CHANGED, actor=admin_user, details={"target_user": user.email, "new_role": role})
    return user

@router.delete("/users/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_uuid: uuid.UUID, db: Session = Depends(get_db), admin_user: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Administrador não pode excluir a si mesmo.")

    log_action(db, action=AuditLogAction.USER_DELETED, actor=admin_user, details={"deleted_user_email": user.email})

    db.query(models.Contract).filter(models.Contract.user_id == user.id).update({"user_id": None})
    db.query(models.Contract).filter(models.Contract.deleted_by_id == user.id).update({"deleted_by_id": None})

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)