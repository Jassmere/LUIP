from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

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

    campaign_name = Column(
        String(255),
        nullable=False,
    )

    campaign_type = Column(
        String(100),
        default="Email",
    )

    subject = Column(
        String(500),
        nullable=True,
    )

    message = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(100),
        default="Draft",
    )

    scheduled_for = Column(
        DateTime,
        nullable=True,
    )

    sent_at = Column(
        DateTime,
        nullable=True,
    )

    opened = Column(
        Boolean,
        default=False,
    )

    clicked = Column(
        Boolean,
        default=False,
    )

    replied = Column(
        Boolean,
        default=False,
    )

    meeting_booked = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship(
        "Company",
    )

    decision_maker = relationship(
        "DecisionMaker",
    )