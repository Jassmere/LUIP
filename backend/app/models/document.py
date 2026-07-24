from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)

    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    file_size = Column(Integer, nullable=False)

    checksum = Column(String, nullable=False)

    version = Column(Integer, default=1)

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
        default=datetime.utcnow,
    )

    # -----------------------------
    # AI Processing Fields
    # -----------------------------

    extracted_text = Column(
        Text,
        nullable=True,
    )

    processing_status = Column(
        String,
        default="Pending",
    )

    processed_at = Column(
        DateTime,
        nullable=True,
    )