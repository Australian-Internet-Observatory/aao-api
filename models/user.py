from uuid import uuid4
from typing import List, TYPE_CHECKING
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from .base import Base

if TYPE_CHECKING:
    from .export import ExportORM, SharedExportORM

class UserORM(Base):
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(nullable=True)  # Made optional
    enabled: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(default="user")
    primary_email: Mapped[str] = mapped_column(nullable=True)  # Made optional
    
    # Add relationship to user_identities
    identities: Mapped[List["UserIdentityORM"]] = relationship("UserIdentityORM", back_populates="user")
    
    # Relationships for exports
    exports: Mapped[List["ExportORM"]] = relationship("ExportORM", back_populates="creator")
    shared_exports: Mapped[List["SharedExportORM"]] = relationship("SharedExportORM", back_populates="user")

class UserIdentityORM(Base):
    __tablename__ = 'user_identities'
    
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    provider: Mapped[str] = mapped_column(primary_key=True)  # 'local' or 'cilogon'
    provider_user_id: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=True)  # Only for local provider
    created_at: Mapped[int] = mapped_column(nullable=False)
    
    # Add relationship back to user
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="identities")

class User(BaseModel):
    id: str
    full_name: str | None = None
    enabled: bool = True
    role: str = "user"
    primary_email: str | None = None

class UserIdentity(BaseModel):
    user_id: str
    provider: str
    provider_user_id: str
    password: str | None = None
    created_at: int