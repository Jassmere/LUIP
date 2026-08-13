"""
add LBIT classification fields

Revision ID: 3b001_lbit_classification
Revises: ae4fb47627e9
Create Date: 2026-08-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b001_lbit_classification"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "ae4fb47627e9"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add LBIT classification fields to buying-intent signals.
    """

    op.add_column(
        "buying_intent_signals",
        sa.Column(
            "lbit_level",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "buying_intent_signals",
        sa.Column(
            "lbit_category",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.add_column(
        "buying_intent_signals",
        sa.Column(
            "lbit_score",
            sa.Float(),
            nullable=True,
        ),
    )

    op.add_column(
        "buying_intent_signals",
        sa.Column(
            "lbit_confidence",
            sa.Float(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_buying_intent_signals_lbit_level",
        "buying_intent_signals",
        ["lbit_level"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove LBIT classification fields.
    """

    op.drop_index(
        "ix_buying_intent_signals_lbit_level",
        table_name="buying_intent_signals",
    )

    op.drop_column(
        "buying_intent_signals",
        "lbit_confidence",
    )

    op.drop_column(
        "buying_intent_signals",
        "lbit_score",
    )

    op.drop_column(
        "buying_intent_signals",
        "lbit_category",
    )

    op.drop_column(
        "buying_intent_signals",
        "lbit_level",
    )