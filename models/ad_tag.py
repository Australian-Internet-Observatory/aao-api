from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class AdTagORM(Base):
    __tablename__ = 'applied_tags'
    
    observation_id: Mapped[str] = mapped_column(primary_key=True)
    tag_id: Mapped[str] = mapped_column(primary_key=True)

class AdTag(BaseModel):
    observation_id: str
    tag_id: str

class LegacyAdTag(BaseModel):
    id: str
    tags: List[str]