from app.db.base import Base
from app.db.session import engine

# Import models
from app.models.user import User


def create_database():
    Base.metadata.create_all(bind=engine)