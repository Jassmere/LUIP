"""Sprint5_AI_Document_Model

Revision ID: 1ed3bb09ac20
Revises:
Create Date: 2026-07-24 16:51:11.954613
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "1ed3bb09ac20"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "documents",
        sa.Column(
            "ai_status",
            sa.String(),
            nullable=False,
            server_default="Pending",
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "text_content",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "summary",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "processing_started_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "processing_completed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("documents", "processing_completed_at")
    op.drop_column("documents", "processing_started_at")
    op.drop_column("documents", "summary")
    op.drop_column("documents", "text_content")
    op.drop_column("documents", "ai_status")