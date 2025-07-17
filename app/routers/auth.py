from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import EmailStr
from typing import Optional

from core import security
from core.database import get_db
from models import models
from schemas import schemas
from models.models import UserRole
from services.audit_service import log_action, AuditLogAction

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_current_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user = get_user(db, email=email)
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas, por favor, faça o login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = get_current_user_from_token(token, db)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=UserRole.USER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_action(db, action=AuditLogAction.USER_CREATED, actor=db_user, details={"email": db_user.email})

    return db_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = get_user(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.email})

    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax")

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(email: EmailStr = Body(..., embed=True), db: Session = Depends(get_db)):
    user = get_user(db, email)
    if not user:
        # Não informamos que o usuário não existe por segurança
        return {"message": "Se um usuário com esse email existir, um link de recuperação será enviado."}

    reset_token = security.create_reset_token(email=email)
    reset_link = f"http://localhost:8000/reset-password-page?token={reset_token}" # Link para uma página frontend

    print("--- LINK DE RESET DE SENHA (PARA FINS DE DEMONSTRAÇÃO) ---")
    print(reset_link)
    print("---------------------------------------------------------")

    return {"message": "Se um usuário com esse email existir, um link de recuperação será enviado."}

@router.post("/reset-password")
def reset_password(token: str, new_password: str = Body(..., embed=True), db: Session = Depends(get_db)):
    email = security.verify_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = get_user(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.hashed_password = security.get_password_hash(new_password)
    db.add(user)
    db.commit()
    log_action(db, action=AuditLogAction.USER_PASSWORD_CHANGED, actor=user)
    return {"message": "Senha alterada com sucesso"}