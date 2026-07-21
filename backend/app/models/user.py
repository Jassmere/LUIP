from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(255), nullable=False)

    email = Column(String(255), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    organizations = relationship(
        "Organization",
        back_populates="owner"
    )

    contracts = relationship(
        "Contract",
        back_populates="creator"
    )

    documents = relationship(
        "Document",
        back_populates="uploader"
    )