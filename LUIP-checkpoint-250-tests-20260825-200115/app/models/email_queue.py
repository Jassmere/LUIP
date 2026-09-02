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


class EmailQueue(Base):
    __tablename__ = "email_queue"

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

    campaign_id = Column(
        Integer,
        ForeignKey("outreach_campaigns.id"),
        nullable=True,
    )

    # =====================================================
    # SMTP PROVIDER
    # =====================================================
    #
    # Supported values:
    #
    #     default
    #     gmail
    #     outlook
    #     zoho
    #
    # "default" preserves backwards compatibility with
    # the original SMTP_* configuration.
    #

    smtp_provider = Column(
        String(50),
        nullable=False,
        default="default",
        server_default="default",
        index=True,
    )

    recipient_email = Column(
        String(255),
        nullable=False,
    )

    recipient_name = Column(
        String(255),
        nullable=True,
    )

    subject = Column(
        String(500),
        nullable=False,
    )

    body = Column(
        Text,
        nullable=False,
    )

    priority = Column(
        String(50),
        default="Normal",
    )

    status = Column(
        String(50),
        default="Pending",
    )

    retry_count = Column(
        Integer,
        default=0,
    )

    max_retries = Column(
        Integer,
        default=5,
    )

    scheduled_for = Column(
        DateTime,
        nullable=True,
    )

    sent_at = Column(
        DateTime,
        nullable=True,
    )

    error_message = Column(
        Text,
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

    bounced = Column(
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

    campaign = relationship(
        "OutreachCampaign",
    )