from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class BuyingActivity(Base):
    __tablename__ = "buying_activities"

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

    decision_maker_id = Column(
        Integer,
        ForeignKey("decision_makers.id"),
        nullable=True,
    )

    activity_type = Column(
        String(150),
        nullable=False,
        index=True,
    )

    activity_source = Column(
        String(150),
        nullable=True,
    )

    title = Column(
        String(500),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    url = Column(
        String(1000),
        nullable=True,
    )

    buying_score = Column(
        Float,
        default=0.0,
    )

    confidence = Column(
        Float,
        default=100.0,
    )

    processed = Column(
        Boolean,
        default=False,
    )

    ai_summary = Column(
        Text,
        nullable=True,
    )

    ai_recommendation = Column(
        Text,
        nullable=True,
    )

    discovered_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    company = relationship(
        "Company",
    )

    decision_maker = relationship(
        "DecisionMaker",
    )