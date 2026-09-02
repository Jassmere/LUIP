from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Index,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
    )

    # ---------------------------------
    # AI Classification
    # ---------------------------------

    clause_type = Column(
        Text,
        nullable=False,
    )

    heading = Column(
        Text,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    confidence_score = Column(
        Float,
        nullable=False,
        default=100.0,
    )

    # ---------------------------------
    # Vega AI Risk Intelligence
    # ---------------------------------

    risk_level = Column(
        String(20),
        nullable=False,
        default="Low",
    )

    risk_score = Column(
        Integer,
        nullable=False,
        default=0,
    )

    recommendation = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------

    page_number = Column(
        Integer,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    document = relationship(
        "Document",
        back_populates="clauses",
    )

    __table_args__ = (
        Index(
            "ix_clauses_document",
            "document_id",
        ),
    )