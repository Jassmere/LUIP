from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    company_type = Column(String(100), nullable=False)

    country = Column(String(100), nullable=False)

    industry = Column(String(100), nullable=False)

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="organizations"
    )

    contracts = relationship(
        "Contract",
        back_populates="organization"
    )