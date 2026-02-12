"""Commercial Content Enrichment ORM model.

Stores metadata about CCL scrape enrichments linked to observations.
Each record represents one CCL scrape instance (identified by ccl_uuid)
for a given observation.
"""

from sqlalchemy import BigInteger, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class CommercialContentEnrichmentORM(Base):
    """ORM model for commercial content library enrichment records.

    Maps to the ``commercial_content_enrichments`` table.  Each row captures
    the canonical metadata for a single CCL scrape tied to an observation.
    """

    __tablename__ = 'commercial_content_enrichments'

    # Primary key — the ccl_uuid from the RDO (or a deterministic fallback)
    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        nullable=False,
    )

    observation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    ad_type: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    vendor: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    scrape_started_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    scrape_completed_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<CommercialContentEnrichment("
            f"id={self.id!r}, observation_id={self.observation_id!r}, "
            f"vendor={self.vendor!r}, version={self.version})>"
        )
