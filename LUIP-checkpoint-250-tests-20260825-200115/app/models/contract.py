from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)

    contract_type = Column(String(100), nullable=False)

    status = Column(String(50), default="Draft")

    counterparty = Column(String(255), nullable=False)

    effective_date = Column(Date, nullable=True)

    expiry_date = Column(Date, nullable=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    organization = relationship(
        "Organization",
        back_populates="contracts"
    )

    creator = relationship(
        "User",
        back_populates="contracts"
    )

    documents = relationship(
        "Document",
        back_populates="contract"
    )