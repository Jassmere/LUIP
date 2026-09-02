from app.db.base import Base
from app.db.session import SessionLocal, engine

# ---------------------------------------------------------
# Existing Models
# ---------------------------------------------------------

from app.models.user import User
from app.models.organization import Organization
from app.models.contract import Contract
from app.models.document import Document
from app.models.clause import Clause

# ---------------------------------------------------------
# Buying Intelligence Models
# ---------------------------------------------------------

from app.models.company import Company
from app.models.company_score import CompanyScore
from app.models.decision_maker import DecisionMaker
from app.models.buying_activity import BuyingActivity
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.next_best_action import NextBestAction
from app.models.email_queue import EmailQueue
from app.models.outreach_campaign import OutreachCampaign

# ---------------------------------------------------------
# Create Database
# ---------------------------------------------------------

def create_database():
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()