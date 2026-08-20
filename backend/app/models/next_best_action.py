from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class NextBestAction(Base):
    __tablename__ = "next_best_actions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    action_type = Column(
        String(100),
        nullable=False,
    )

    priority = Column(
        String(50),
        nullable=False,
    )

    recommended_within_hours = Column(
        Integer,
        nullable=False,
        default=48,
    )

    explanation = Column(
        Text,
        nullable=False,
    )

    ai_reasoning = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        default="Pending",
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    completed_at = Column(
        DateTime,
        nullable=True,
    )

    company = relationship(
        "Company",
    )