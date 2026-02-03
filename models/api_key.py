from uuid import uuid4
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, BigInteger
from .base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserORM

class ApiKeyORM(Base):
    __tablename__ = 'api_keys'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    suffix: Mapped[str] = mapped_column(String(6), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_used_at: Mapped[int] = mapped_column(BigInteger, nullable=True)
    
    # Relationship to user
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="api_keys")

class ApiKey(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None = None
    hashed_key: str
    suffix: str  # last 6 characters
    created_at: int
    last_used_at: int | None = None

class ApiKeyCreate(BaseModel):
    title: str
    description: str | None = None

class ApiKeyWithSecret(BaseModel):
    """Response model for API key creation that includes the full key"""
    id: str
    user_id: str
    title: str
    description: str | None = None
    suffix: str
    key: str  # The full API key (only shown once)
    created_at: int
