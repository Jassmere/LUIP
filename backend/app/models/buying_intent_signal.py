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
    """
    LUIP Buying Intent Signal.

    Stores a detected buying-intent signal together with
    its original LUIP scoring information and, where a
    verified taxonomy rule exists, its LBIT classification.
    """

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

    # ---------------------------------------------------------
    # LUIP BUYING-INTENT SCORING
    # ---------------------------------------------------------

    score = Column(
        Float,
        default=0,
    )

    confidence = Column(
        Float,
        default=100,
    )

    # ---------------------------------------------------------
    # LBIT CLASSIFICATION
    # ---------------------------------------------------------

    lbit_level = Column(
        Integer,
        nullable=True,
        index=True,
    )

    lbit_category = Column(
        String(150),
        nullable=True,
    )

    lbit_score = Column(
        Float,
        nullable=True,
    )

    lbit_confidence = Column(
        Float,
        nullable=True,
    )

    # ---------------------------------------------------------
    # DETECTION TIMESTAMP
    # ---------------------------------------------------------

    detected_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    # ---------------------------------------------------------
    # COMPANY RELATIONSHIP
    # ---------------------------------------------------------

    company = relationship(
        "Company",
        back_populates="buying_signals",
    )