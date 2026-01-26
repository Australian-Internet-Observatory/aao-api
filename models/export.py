from uuid import uuid4
from typing import List, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, DateTime, Enum as SQLEnum
from .base import Base

if TYPE_CHECKING:
    from .user import UserORM


class ExportStatus(str, Enum):
    """Enum representing the status of an export job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportORM(Base):
    """ORM model for export jobs."""
    __tablename__ = 'exports'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    creator_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    include_images: Mapped[bool] = mapped_column(default=False)
    query_string: Mapped[str] = mapped_column(Text, nullable=True)  # Serialized query parameters (JSON)
    status: Mapped[str] = mapped_column(
        SQLEnum(ExportStatus, values_callable=lambda x: [e.value for e in x]),
        default=ExportStatus.PENDING
    )
    object_location: Mapped[str] = mapped_column(Text, nullable=True)  # Location of the exported file in S3
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)  # Error message if export fails
    
    # Relationships
    creator: Mapped["UserORM"] = relationship("UserORM", back_populates="exports")
    shared_with: Mapped[List["SharedExportORM"]] = relationship(
        "SharedExportORM",
        back_populates="export",
        cascade="all, delete-orphan"
    )
    fields: Mapped[List["ExportFieldORM"]] = relationship(
        "ExportFieldORM",
        back_populates="export",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Export(id={self.id}, creator_id={self.creator_id}, status={self.status})>"


class SharedExportORM(Base):
    """ORM model for sharing exports with other users."""
    __tablename__ = 'shared_exports'
    
    export_id: Mapped[str] = mapped_column(ForeignKey('exports.id'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    
    # Relationships
    export: Mapped["ExportORM"] = relationship("ExportORM", back_populates="shared_with")
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="shared_exports")

    def __repr__(self):
        return f"<SharedExport(export_id={self.export_id}, user_id={self.user_id})>"


class ExportableFieldORM(Base):
    """ORM model for exportable fields that users can select for exports."""
    __tablename__ = 'exportable_fields'
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(nullable=False, unique=True)  # e.g., 'OCR Text'
    description: Mapped[str] = mapped_column(Text, nullable=True)  # Description of the field
    path: Mapped[str] = mapped_column(nullable=False)  # Dot notation path, e.g., 'ocr.text'
    is_default: Mapped[bool] = mapped_column(default=False)  # Whether this field is included by default
    
    # Relationships
    export_fields: Mapped[List["ExportFieldORM"]] = relationship(
        "ExportFieldORM",
        back_populates="field"
    )

    def __repr__(self):
        return f"<ExportableField(id={self.id}, name={self.name}, path={self.path})>"


class ExportFieldORM(Base):
    """ORM model for mapping exports to their selected fields."""
    __tablename__ = 'export_fields'
    
    export_id: Mapped[str] = mapped_column(ForeignKey('exports.id'), primary_key=True)
    field_id: Mapped[str] = mapped_column(ForeignKey('exportable_fields.id'), primary_key=True)
    
    # Relationships
    export: Mapped["ExportORM"] = relationship("ExportORM", back_populates="fields")
    field: Mapped["ExportableFieldORM"] = relationship("ExportableFieldORM", back_populates="export_fields")

    def __repr__(self):
        return f"<ExportField(export_id={self.export_id}, field_id={self.field_id})>"


# Pydantic models for API serialization
from pydantic import BaseModel
from typing import Optional


class Export(BaseModel):
    """Pydantic model for Export API responses."""
    id: str
    creator_id: str
    include_images: bool = False
    query_string: Optional[str] = None
    status: str = "pending"
    object_location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    message: Optional[str] = None


class SharedExport(BaseModel):
    """Pydantic model for SharedExport API responses."""
    export_id: str
    user_id: str


class ExportableField(BaseModel):
    """Pydantic model for ExportableField API responses."""
    id: str
    name: str
    description: Optional[str] = None
    path: str
    is_default: bool = False


class ExportField(BaseModel):
    """Pydantic model for ExportField API responses."""
    export_id: str
    field_id: str
