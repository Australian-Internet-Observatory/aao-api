from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class AdAttributeORM(Base):
    __tablename__ = 'ad_attributes'
    
    observation_id: Mapped[str] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column()
    created_at: Mapped[int] = mapped_column()
    created_by: Mapped[str] = mapped_column()
    modified_at: Mapped[int] = mapped_column()
    modified_by: Mapped[str] = mapped_column()

class AdAttribute(BaseModel):
    observation_id: str
    key: str
    value: str
    created_at: int
    created_by: str
    modified_at: int
    modified_by: str