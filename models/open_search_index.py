from pydantic import BaseModel
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class OpenSearchIndexORM(Base):
    __tablename__ = 'open_search_indices'
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

class OpenSearchIndex(BaseModel):
    id: str # auto-generated UUID
    name: str # name of the index
    created_at: int
    status: str # e.g., "created", "in progress", "ready"