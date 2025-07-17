from fastapi import APIRouter, Request, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from core.database import get_db
from routers.auth import get_current_user_from_token

router = APIRouter(tags=["Frontend"])
templates = Jinja2Templates(directory="templates")

def get_user_from_cookie(request: Request, access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if access_token:
        token = access_token.split("Bearer ")[-1]
        user = get_current_user_from_token(token, db)
        return user
    return None

@router.get("/", response_class=HTMLResponse)
async def read_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/reset-password-page", response_class=HTMLResponse)
async def read_reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, user: dict = Depends(get_user_from_cookie)):
    if not user: return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.get("/profile", response_class=HTMLResponse)
async def read_profile_page(request: Request, user: dict = Depends(get_user_from_cookie)):
    if not user: return RedirectResponse(url="/", status_code=302)
    user_uuid_param = request.query_params.get('user_uuid')
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "user_uuid_to_edit": user_uuid_param})

@router.get("/contracts-list", response_class=HTMLResponse)
async def read_contracts_list_page(request: Request, user: dict = Depends(get_user_from_cookie)):
    if not user: return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("contracts_list.html", {"request": request, "user": user})

@router.get("/contracts/{contract_id}/view", response_class=HTMLResponse)
async def read_contract_view_page(request: Request, contract_id: int, user: dict = Depends(get_user_from_cookie)):
    if not user: return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("contract_view.html", {"request": request, "contract_id": contract_id, "user": user})

@router.get("/admin/users", response_class=HTMLResponse)
async def read_admin_users_page(request: Request, user: dict = Depends(get_user_from_cookie)):
    if not user or user.role != 'ADMIN':
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": user})