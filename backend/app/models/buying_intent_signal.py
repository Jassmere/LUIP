from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class BuyingIntentSignal(Base):
    __tablename__ = "buying_intent_signals"

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

    signal_name = Column(
        String(255),
        nullable=False,
    )

    signal_category = Column(
        String(100),
        nullable=False,
    )

    source = Column(
        String(255),
        nullable=True,
    )

    source_url = Column(
        String(1000),
        nullable=True,
    )

    evidence = Column(
        Text,
        nullable=True,
    )

    score = Column(
        Float,
        default=0,
    )

    confidence = Column(
        Float,
        default=100,
    )

    detected_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    company = relationship(
        "Company",
        back_populates="buying_signals",
    )