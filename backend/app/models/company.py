from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    website = Column(
        String(500),
        nullable=True,
    )

    linkedin_url = Column(
        String(500),
        nullable=True,
    )

    industry = Column(
        String(255),
        nullable=True,
    )

    country = Column(
        String(100),
        nullable=True,
    )

    city = Column(
        String(100),
        nullable=True,
    )

    company_size = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    discovered_from = Column(
        String(255),
        nullable=True,
    )

    # -----------------------------
    # Discovery Intelligence
    # -----------------------------

    last_scan = Column(
        DateTime,
        nullable=True,
    )

    scan_status = Column(
        String(50),
        default="Pending",
    )

    active = Column(
        Boolean,
        default=True,
    )

    # -----------------------------
    # Audit
    # -----------------------------

    discovery_date = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # -----------------------------
    # Relationships
    # -----------------------------

    buying_signals = relationship(
        "BuyingIntentSignal",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    company_score = relationship(
        "CompanyScore",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )

    decision_makers = relationship(
        "DecisionMaker",
        back_populates="company",
        cascade="all, delete-orphan",
    )