# app/models/models.py
import uuid
import enum
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, 
                        JSON, Enum as SQLAlchemyEnum, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, index=True, nullable=True)
    last_name = Column(String, index=True, nullable=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)

    contracts = relationship("Contract", foreign_keys="[Contract.user_id]", back_populates="owner")

class ContractStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(SQLAlchemyEnum(ContractStatus), default=ContractStatus.PENDING)
    extracted_data = Column(JSON, nullable=True)
    analysis_summary = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[user_id], back_populates="contracts")
    deleter = relationship("User", foreign_keys=[deleted_by_id])

class AuditLogAction(str, enum.Enum):
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    USER_PASSWORD_CHANGED = "USER_PASSWORD_CHANGED"
    CONTRACT_DELETED = "CONTRACT_DELETED"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Quem fez a ação
    action = Column(SQLAlchemyEnum(AuditLogAction), nullable=False)
    details = Column(JSON, nullable=True)

    actor = relationship("User")