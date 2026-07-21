from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String(255), nullable=False)

    original_filename = Column(String(255), nullable=False)

    file_type = Column(String(50), nullable=False)

    file_path = Column(String(500), nullable=False)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    contract = relationship(
        "Contract",
        back_populates="documents"
    )

    uploader = relationship(
        "User",
        back_populates="documents"
    )