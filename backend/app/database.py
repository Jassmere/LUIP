from app.db.base import Base
from app.db.session import engine

# Import every SQLAlchemy model.
# This registers all relationships before create_all() executes.

from app.models.user import User
from app.models.organization import Organization
from app.models.contract import Contract
from app.models.document import Document


def create_database():
    Base.metadata.create_all(bind=engine)