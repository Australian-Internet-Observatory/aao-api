"""Advertisement Snapshot ORM model.

Stores advertisement snapshots captured during a CCL enrichment scrape.
Each record represents the state of an advertisement on the advertising
platform at the time of scraping.
"""

from uuid import uuid4

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdvertisementSnapshotORM(Base):
    """ORM model for advertisement snapshot records.

    Maps to the ``advertisement_snapshots`` table.  The full snapshot
    object is stored in a JSONB ``data`` column; ``source_id`` is
    extracted for indexing/querying.
    """

    __tablename__ = 'advertisement_snapshots'

    __table_args__ = (
        # Deduplicate when source_id is present
        UniqueConstraint(
            'ccl_enrichment_id', 'source_id',
            name='uq_snapshot_enrichment_source',
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

    data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    def __repr__(self) -> str:
        return (
            f"<AdvertisementSnapshot("
            f"id={self.id!r}, ccl_enrichment_id={self.ccl_enrichment_id!r}, "
            f"source_id={self.source_id!r})>"
        )
