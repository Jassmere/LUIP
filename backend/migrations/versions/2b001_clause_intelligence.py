"""Sprint 11 - Clause Intelligence

Revision ID: 2b001_clause_intelligence
Revises: 1ed3bb09ac20
Create Date: 2026-07-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "2b001_clause_intelligence"
down_revision = "1ed3bb09ac20"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "clauses",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),

        sa.Column(
            "clause_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "heading",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=False,
            server_default="100",
        ),

        sa.Column(
            "page_number",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_clauses_id",
        "clauses",
        ["id"],
    )

    op.create_index(
        "ix_clauses_document",
        "clauses",
        ["document_id"],
    )


def downgrade():

    op.drop_index(
        "ix_clauses_document",
        table_name="clauses",
    )

    op.drop_index(
        "ix_clauses_id",
        table_name="clauses",
    )

    op.drop_table("clauses")