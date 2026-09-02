"""
LUIP SQLAlchemy model registry.

Import all application models from this module so that SQLAlchemy
can resolve relationship() targets before mapper configuration.
"""

from app.models.user import User
from app.models.organization import Organization
from app.models.contract import Contract
from app.models.document import Document
from app.models.clause import Clause

from app.models.company import Company
from app.models.company_score import CompanyScore
from app.models.decision_maker import DecisionMaker
from app.models.buying_activity import BuyingActivity
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.next_best_action import NextBestAction

from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue


__all__ = [
    "User",
    "Organization",
    "Contract",
    "Document",
    "Clause",
    "Company",
    "CompanyScore",
    "DecisionMaker",
    "BuyingActivity",
    "BuyingIntentSignal",
    "NextBestAction",
    "OutreachCampaign",
    "EmailQueue",
]
