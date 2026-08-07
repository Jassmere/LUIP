from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class CompanyScore(Base):
    __tablename__ = "company_scores"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    buying_intent_score = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    priority = Column(
        String(50),
        nullable=False,
        default="Low",
    )

    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship(
        "Company",
        back_populates="company_score",
    )