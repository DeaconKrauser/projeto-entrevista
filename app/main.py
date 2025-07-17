# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.database import Base, engine
from models import models
from routers import auth, contracts, pages, users, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contract Analysis API",
    description="API para upload, análise e consulta de contratos.",
    version="1.0.0"
)

# Monta arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rotas de API com prefixo /api
app.include_router(auth.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Rotas de páginas (frontend) sem prefixo
app.include_router(pages.router)