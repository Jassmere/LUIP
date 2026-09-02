"""add email smtp provider

Revision ID: d7a001
Revises: c989670e0fa6
Create Date: 2026-08-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7a001"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "c989670e0fa6"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    """Add SMTP provider routing to email queue."""

    op.add_column(
        "email_queue",
        sa.Column(
            "smtp_provider",
            sa.String(length=50),
            nullable=False,
            server_default="default",
        ),
    )

    op.create_index(
        "ix_email_queue_smtp_provider",
        "email_queue",
        ["smtp_provider"],
        unique=False,
    )


def downgrade() -> None:
    """Remove SMTP provider routing from email queue."""

    op.drop_index(
        "ix_email_queue_smtp_provider",
        table_name="email_queue",
    )

    op.drop_column(
        "email_queue",
        "smtp_provider",
    )