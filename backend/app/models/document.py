from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    filename = Column(
        String,
        nullable=False,
    )

    original_filename = Column(
        String,
        nullable=False,
    )

    file_type = Column(
        String,
        nullable=False,
    )

    file_path = Column(
        String,
        nullable=False,
    )

    file_size = Column(
        Integer,
        nullable=False,
    )

    checksum = Column(
        String,
        nullable=False,
    )

    version = Column(
        Integer,
        default=1,
        nullable=False,
    )

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False,
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    uploaded_at = Column(
        DateTime,
        nullable=False,
    )

    ai_status = Column(
        String,
        default="Pending",
        nullable=False,
    )

    text_content = Column(
        Text,
        nullable=True,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    processing_started_at = Column(
        DateTime,
        nullable=True,
    )

    processing_completed_at = Column(
        DateTime,
        nullable=True,
    )

    contract = relationship(
        "Contract",
        back_populates="documents",
    )

    uploader = relationship(
        "User",
        back_populates="documents",
    )

    clauses = relationship(
        "Clause",
        back_populates="document",
        cascade="all, delete-orphan",
    )