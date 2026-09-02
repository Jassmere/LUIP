"""add company discovery fields

Revision ID: ae4fb47627e9
Revises: 2b002_ai_risk_engine
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ae4fb47627e9"
down_revision: Union[str, Sequence[str], None] = "2b002_ai_risk_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing company discovery fields."""

    op.add_column(
        "companies",
        sa.Column(
            "last_scan",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "companies",
        sa.Column(
            "scan_status",
            sa.String(length=50),
            nullable=True,
            server_default="Pending",
        ),
    )


def downgrade() -> None:
    """Remove company discovery fields."""

    op.drop_column("companies", "scan_status")
    op.drop_column("companies", "last_scan")
