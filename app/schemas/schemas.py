# app/schemas/schemas.py
import uuid
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.models import ContractStatus, UserRole

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class User(UserBase):
    id: int
    uuid: uuid.UUID
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ContractBase(BaseModel):
    filename: str
    status: ContractStatus
    extracted_data: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None

class ContractDetails(ContractBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True