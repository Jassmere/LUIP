"""Sprint 12 - AI Risk Intelligence

Revision ID: 2b002_ai_risk_engine
Revises: 2b001_clause_intelligence
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "2b002_ai_risk_engine"
down_revision = "2b001_clause_intelligence"
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        "clauses",
        sa.Column(
            "risk_level",
            sa.String(length=20),
            nullable=False,
            server_default="Low",
        ),
    )

    op.add_column(
        "clauses",
        sa.Column(
            "risk_score",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "clauses",
        sa.Column(
            "recommendation",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade():

    op.drop_column(
        "clauses",
        "recommendation",
    )

    op.drop_column(
        "clauses",
        "risk_score",
    )

    op.drop_column(
        "clauses",
        "risk_level",
    )