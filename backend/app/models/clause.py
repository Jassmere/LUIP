from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
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

    clause_type = Column(
        String(100),
        nullable=False,
    )

    heading = Column(
        String(255),
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

    # -----------------------------
    # AI Risk Intelligence
    # -----------------------------

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

    # -----------------------------

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