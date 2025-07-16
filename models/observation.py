from pydantic import BaseModel
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class ObservationORM(Base):
    __tablename__ = 'observations'
    
    observation_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True,
        nullable=False
    )
    observer_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False
    )
    timestamp: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

class Observation(BaseModel):
    observer_id: str
    observation_id: str
    timestamp: int