from uuid import uuid4
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class TagORM(Base):
    __tablename__ = 'tags'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    hex: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, description={self.description}, hex={self.hex})>"

class Tag(BaseModel):
    id: str
    name: str
    description: str
    hex: str