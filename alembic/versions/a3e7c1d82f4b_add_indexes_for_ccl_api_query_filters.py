"""add indexes for ccl api query filters

Revision ID: a3e7c1d82f4b
Revises: 9f78b27ced9c
Create Date: 2026-02-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3e7c1d82f4b'
down_revision: Union[str, Sequence[str], None] = '9f78b27ced9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes on CCL filter columns used by the /ccl/* API endpoints."""
    op.create_index(
        'ix_commercial_content_enrichments_platform',
        'commercial_content_enrichments',
        ['platform'],
        unique=False,
    )
    op.create_index(
        'ix_commercial_content_enrichments_scrape_started_at',
        'commercial_content_enrichments',
        ['scrape_started_at'],
        unique=False,
    )
    op.create_index(
        'ix_commercial_content_enrichments_scrape_completed_at',
        'commercial_content_enrichments',
        ['scrape_completed_at'],
        unique=False,
    )
    op.create_index(
        'ix_advertising_entities_type',
        'advertising_entities',
        ['type'],
        unique=False,
    )


def downgrade() -> None:
    """Remove CCL filter indexes."""
    op.drop_index('ix_advertising_entities_type', table_name='advertising_entities')
    op.drop_index('ix_commercial_content_enrichments_scrape_completed_at', table_name='commercial_content_enrichments')
    op.drop_index('ix_commercial_content_enrichments_scrape_started_at', table_name='commercial_content_enrichments')
    op.drop_index('ix_commercial_content_enrichments_platform', table_name='commercial_content_enrichments')
