from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class DecisionMaker(Base):
    __tablename__ = "decision_makers"

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

    full_name = Column(
        String(255),
        nullable=True,
    )

    title = Column(
        String(255),
        nullable=True,
    )

    department = Column(
        String(150),
        nullable=True,
    )

    email = Column(
        String(255),
        nullable=True,
        index=True,
    )

    phone = Column(
        String(100),
        nullable=True,
    )

    linkedin = Column(
        String(500),
        nullable=True,
    )

    seniority = Column(
        String(100),
        nullable=True,
    )

    source = Column(
        String(255),
        nullable=True,
    )

    verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship(
        "Company",
        back_populates="decision_makers",
    )