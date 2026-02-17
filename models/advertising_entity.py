"""Advertising Entity ORM model.

Stores advertising entities (pages, keywords, locations, etc.) discovered
during a CCL enrichment scrape.  Each record is a snapshot of an entity
at a particular scrape time.
"""

from uuid import uuid4

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdvertisingEntityORM(Base):
    """ORM model for advertising entity snapshots.

    Maps to the ``advertising_entities`` table.  Each row stores the raw
    entity data in a JSONB ``data`` column, with canonical fields
    (``source_id``, ``type``) extracted for querying.
    """

    __tablename__ = 'advertising_entities'

    __table_args__ = (
        # Deduplicate when source_id is present
        UniqueConstraint(
            'ccl_enrichment_id', 'source_id', 'type',
            name='uq_entity_enrichment_source_type',
        ),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False,
    )

    ccl_enrichment_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    source_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    def __repr__(self) -> str:
        return (
            f"<AdvertisingEntity("
            f"id={self.id!r}, ccl_enrichment_id={self.ccl_enrichment_id!r}, "
            f"type={self.type!r}, source_id={self.source_id!r})>"
        )
