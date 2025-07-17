import asyncio
import json
from typing import List, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette.responses import StreamingResponse

from core.database import get_db
from core.cache import cache
from models import models
from schemas import schemas
from routers.auth import get_current_user
from services import file_processor, ai_service, audit_service
from models.models import UserRole, AuditLogAction

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/stats")
def get_contract_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Contract).filter(models.Contract.is_deleted == False)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(models.Contract.user_id == current_user.id)
    
    success_count = query.filter(models.Contract.status == models.ContractStatus.SUCCESS).count()
    error_count = query.filter(models.Contract.status == models.ContractStatus.ERROR).count()
    pending_count = query.filter(models.Contract.status == models.ContractStatus.PENDING).count()

    return {"analyzed": success_count, "pending": pending_count, "error": error_count }

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_contract(
    file: UploadFile,
    ai_provider: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    file_content = await file.read()
    filename = file.filename

    new_contract = models.Contract(filename=filename, user_id=current_user.id, status=models.ContractStatus.PENDING)
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    async def event_generator(contract_id: int, content: bytes, name: str) -> AsyncGenerator[str, None]:
        contract_to_update = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
        yield f"data: Iniciando processo para o arquivo: {name}\n\n"
        await asyncio.sleep(1)

        try:
            yield "data: Extraindo texto do arquivo...\n\n"
            texto_extraido = await file_processor.extract_text(content, name)
            if not texto_extraido:
                raise ValueError("Não foi possível extrair texto do arquivo.")

            yield f"data: Enviando para análise da IA com {ai_provider}...\n\n"
            dados_analisados = await ai_service.extract_contract_data(texto_extraido, ai_provider)
            if dados_analisados.get("error"):
                raise ValueError(f"Erro da IA: {dados_analisados.get('details')}")

            contract_to_update.extracted_data = dados_analisados
            contract_to_update.status = models.ContractStatus.SUCCESS
            yield f"data: Finalizado! Contrato '{name}' analisado com sucesso.\n\n"
        except Exception as e:
            contract_to_update.status = models.ContractStatus.ERROR
            contract_to_update.analysis_summary = str(e)
            yield f"data: ERRO: {str(e)}\n\n"
        finally:
            db.commit()

    return StreamingResponse(event_generator(new_contract.id, file_content, filename), media_type="text/event-stream")

@router.get("/", response_model=List[schemas.ContractDetails])
def list_user_contracts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Contract).filter(models.Contract.is_deleted == False)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(models.Contract.user_id == current_user.id)
    
    contracts = query.order_by(models.Contract.created_at.desc()).all()
    return contracts

@router.get("/{contract_id}", response_model=schemas.ContractDetails)
async def get_contract_details(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    cache_key = f"contract:{contract_id}:{current_user.uuid}"
    cached_contract = await cache.get(cache_key)
    if cached_contract:
        try:
            return json.loads(cached_contract)
        except json.JSONDecodeError:
            pass
    
    query = db.query(models.Contract).filter(
        models.Contract.id == contract_id,
        models.Contract.is_deleted == False
    )
    contract = query.first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")

    is_owner = contract.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="Você não tem permissão para ver este contrato")
    
    contract_details = schemas.ContractDetails.from_orm(contract)
    await cache.set(cache_key, contract_details.model_dump_json(), ex=3600)
    return contract

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contract_to_delete = db.query(models.Contract).filter(
        models.Contract.id == contract_id,
        models.Contract.is_deleted == False
    ).first()
    if not contract_to_delete:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")

    is_owner = contract_to_delete.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not is_owner and not is_admin:
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir este contrato")

    contract_to_delete.is_deleted = True
    contract_to_delete.deleted_at = datetime.utcnow()
    contract_to_delete.deleted_by_id = current_user.id
    
    audit_service.log_action(
        db=db,
        action=AuditLogAction.CONTRACT_DELETED,
        actor=current_user,
        details={"contract_id": contract_id, "filename": contract_to_delete.filename}
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)