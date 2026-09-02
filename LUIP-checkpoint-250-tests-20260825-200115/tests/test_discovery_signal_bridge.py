from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.db.base import Base

# ---------------------------------------------------------
# IMPORTANT MODEL REGISTRATION
# ---------------------------------------------------------
# BuyingActivity contains a foreign key to:
#
#     decision_makers.id
#
# SQLAlchemy must have the DecisionMaker model registered
# in Base.metadata before create_all() is called.
from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.buying_activity import BuyingActivity

from app.services.discovery_signal_bridge import (
    DiscoverySignalBridge,
)


# =========================================================
# TEST DATABASE
# =========================================================

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={
        "check_same_thread": False,
    },
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------
# DATABASE FIXTURE
# ---------------------------------------------------------

@pytest.fixture
def db():
    """
    Create a clean SQLite database for every test.
    """

    Base.metadata.create_all(
        bind=engine
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()

        Base.metadata.drop_all(
            bind=engine
        )


# ---------------------------------------------------------
# COMPANY FIXTURE
# ---------------------------------------------------------

@pytest.fixture
def company(db):
    """
    Create a test company.
    """

    company = Company(
        name="Discovery Bridge Test Company",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


# =========================================================
# BRIDGE STATUS
# =========================================================

def test_bridge_status():

    result = DiscoverySignalBridge.status()

    assert result["bridge"] == (
        "LUIP Discovery Signal Bridge"
    )

    assert result["version"] == "1.0.0"

    assert result["status"] == "Ready"

    assert result["website_signals"] == "Active"

    assert result["linkedin_signals"] == "Active"

    assert (
        result["direct_linkedin_scraping"]
        is False
    )


# =========================================================
# PROFILE FLATTENING
# =========================================================

def test_flatten_profile_dictionary():

    profile = {
        "about": "Legal technology company",
        "departments": {
            "legal": "Legal Operations",
        },
    }

    result = (
        DiscoverySignalBridge._flatten_profile(
            profile
        )
    )

    assert "Legal technology company" in result

    assert "Legal Operations" in result


def test_flatten_profile_list():

    profile = [
        "Contract Manager",
        "Legal Operations",
        "Commercial Contracts",
    ]

    result = (
        DiscoverySignalBridge._flatten_profile(
            profile
        )
    )

    assert "Contract Manager" in result

    assert "Legal Operations" in result

    assert "Commercial Contracts" in result


def test_flatten_profile_empty():

    result = (
        DiscoverySignalBridge._flatten_profile(
            None
        )
    )

    assert result == ""


def test_flatten_profile_nested_structure():

    profile = {
        "company": {
            "name": "Test Company",
            "departments": [
                "Legal Operations",
                "Commercial Contracts",
            ],
        },
        "employees": [
            {
                "title": "Contract Manager",
            },
        ],
    }

    result = (
        DiscoverySignalBridge._flatten_profile(
            profile
        )
    )

    assert "Test Company" in result

    assert "Legal Operations" in result

    assert "Commercial Contracts" in result

    assert "Contract Manager" in result


# =========================================================
# WEBSITE SIGNALS
# =========================================================

def test_website_signals_requires_company():

    result = DiscoverySignalBridge.website_signals(
        db=None,
        company=None,
        discovery_result=None,
    )

    assert result["success"] is False

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_website_signals_empty_result(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=None,
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_website_signals_unsuccessful_scan(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": False,
        },
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []

    assert (
        result["reason"]
        == "Website scan unsuccessful."
    )


def test_website_signals_no_matching_terms(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": "Company Homepage",
            "description": (
                "A general technology company."
            ),
            "text": (
                "We provide business services."
            ),
            "final_url": (
                "https://example.com"
            ),
        },
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_website_signal_creates_buying_signal(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": (
                "Enterprise Contract Management Platform"
            ),
            "description": (
                "We provide contract lifecycle "
                "management and contract automation."
            ),
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
    )

    assert result["success"] is True

    assert result["signals_created"] >= 1

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    assert len(signals) >= 1


def test_website_signal_contains_correct_data(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": "Contract Management",
            "description": "",
            "text": "",
            "final_url": (
                "https://example.com/contracts"
            ),
        },
    )

    assert result["signals_created"] == 1

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert (
        signal.signal_name
        == "Website mentions contract management"
    )

    assert (
        signal.signal_category
        == "Website Intelligence"
    )

    assert signal.source == "Website Scanner"

    assert (
        signal.source_url
        == "https://example.com/contracts"
    )

    assert signal.score == 35.0

    assert signal.confidence == 80.0


def test_website_signal_creates_buying_activity(
    db,
    company,
):

    DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": "Contract Management",
            "description": "",
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
    )

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(activities) == 1

    activity = activities[0]

    assert (
        activity.activity_type
        == "Website Intelligence"
    )

    assert (
        activity.activity_source
        == "Website Scanner"
    )

    assert (
        activity.title
        == "Website mentions contract management"
    )

    assert activity.buying_score == 35.0

    assert activity.confidence == 80.0

    assert activity.processed is False


# =========================================================
# LINKEDIN SIGNALS
# =========================================================

def test_linkedin_signals_requires_company():

    result = DiscoverySignalBridge.linkedin_signals(
        db=None,
        company=None,
        discovery_result=None,
    )

    assert result["success"] is False

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_linkedin_signals_empty_result(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result=None,
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_linkedin_signals_unsuccessful_scan(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": False,
        },
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []

    assert (
        result["reason"]
        == "LinkedIn data unavailable."
    )


def test_linkedin_signals_invalid_profile(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": "not-a-dictionary",
        },
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []

    assert (
        result["reason"]
        == "LinkedIn profile data is not structured."
    )


def test_linkedin_signals_no_matching_terms(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": (
                    "General technology company."
                ),
            },
        },
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_linkedin_signal_creates_buying_signal(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": (
                    "We are expanding our "
                    "legal operations team."
                ),
            },
        },
    )

    assert result["success"] is True

    assert result["signals_created"] >= 1

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    assert len(signals) >= 1


def test_linkedin_signal_contains_correct_data(
    db,
    company,
):

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": "Legal Operations",
            },
        },
    )

    assert result["signals_created"] == 1

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert (
        signal.signal_name
        == "LinkedIn intelligence: legal operations"
    )

    assert (
        signal.signal_category
        == "LinkedIn Intelligence"
    )

    assert signal.source == "TestProvider"

    assert (
        signal.source_url
        == "https://linkedin.com/company/example"
    )

    assert signal.score == 40.0

    assert signal.confidence == 75.0


def test_linkedin_signal_creates_buying_activity(
    db,
    company,
):

    DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": "Legal Operations",
            },
        },
    )

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(activities) == 1

    activity = activities[0]

    assert (
        activity.activity_type
        == "LinkedIn Intelligence"
    )

    assert (
        activity.activity_source
        == "TestProvider"
    )

    assert (
        activity.title
        == "LinkedIn intelligence: legal operations"
    )

    assert activity.buying_score == 40.0

    assert activity.confidence == 75.0

    assert activity.processed is False


# =========================================================
# COMBINED DISCOVERY PROCESSING
# =========================================================

def test_process_discovery_requires_company():

    result = DiscoverySignalBridge.process_discovery(
        db=None,
        company=None,
        website_result=None,
        linkedin_result=None,
    )

    assert result["success"] is False

    assert result["signals_created"] == 0


def test_process_discovery_with_no_results(
    db,
    company,
):

    result = DiscoverySignalBridge.process_discovery(
        db=db,
        company=company,
        website_result=None,
        linkedin_result=None,
    )

    assert result["success"] is True

    assert result["company_id"] == company.id

    assert (
        result["company"]
        == company.name
    )

    assert result["signals_created"] == 0

    assert "website" in result

    assert "linkedin" in result


def test_process_discovery_website_only(
    db,
    company,
):

    result = DiscoverySignalBridge.process_discovery(
        db=db,
        company=company,
        website_result={
            "success": True,
            "title": (
                "Contract Lifecycle Management"
            ),
            "description": (
                "Contract automation platform."
            ),
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
        linkedin_result=None,
    )

    assert result["success"] is True

    assert result["signals_created"] >= 1

    assert (
        result["website"]["signals_created"]
        >= 1
    )

    assert (
        result["linkedin"]["signals_created"]
        == 0
    )


def test_process_discovery_linkedin_only(
    db,
    company,
):

    result = DiscoverySignalBridge.process_discovery(
        db=db,
        company=company,
        website_result=None,
        linkedin_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": (
                    "Legal Operations"
                ),
            },
        },
    )

    assert result["success"] is True

    assert result["signals_created"] >= 1

    assert (
        result["website"]["signals_created"]
        == 0
    )

    assert (
        result["linkedin"]["signals_created"]
        >= 1
    )


def test_process_discovery_website_and_linkedin(
    db,
    company,
):

    result = DiscoverySignalBridge.process_discovery(
        db=db,
        company=company,
        website_result={
            "success": True,
            "title": (
                "Contract Lifecycle Management"
            ),
            "description": (
                "Contract automation platform."
            ),
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
        linkedin_result={
            "success": True,
            "linkedin_url": (
                "https://linkedin.com/company/example"
            ),
            "provider": "TestProvider",
            "profile": {
                "about": (
                    "Legal Operations"
                ),
            },
        },
    )

    assert result["success"] is True

    assert (
        result["company_id"]
        == company.id
    )

    assert (
        result["company"]
        == company.name
    )

    assert (
        result["website"]["signals_created"]
        >= 1
    )

    assert (
        result["linkedin"]["signals_created"]
        >= 1
    )

    assert (
        result["signals_created"]
        ==
        result["website"]["signals_created"]
        +
        result["linkedin"]["signals_created"]
    )

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(signals) >= 2

    assert len(activities) >= 2


# =========================================================
# LBIT BEHAVIOUR
# =========================================================

def test_discovery_signals_remain_unclassified_when_not_lbit(
    db,
    company,
):

    DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": "Contract Management",
            "description": "",
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
    )

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert signal.lbit_level is None

    assert signal.lbit_category is None

    assert signal.lbit_score is None

    assert signal.lbit_confidence is None


# =========================================================
# MULTIPLE WEBSITE SIGNALS
# =========================================================

def test_multiple_website_indicators_create_multiple_signals(
    db,
    company,
):

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": (
                "Contract Management and LegalTech"
            ),
            "description": (
                "Contract lifecycle management, "
                "legal operations and document automation."
            ),
            "text": (
                "Our CLM platform provides "
                "contract automation."
            ),
            "final_url": (
                "https://example.com"
            ),
        },
    )

    assert result["success"] is True

    assert result["signals_created"] >= 1

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    assert (
        len(signals)
        == result["signals_created"]
    )


# =========================================================
# SIGNAL / ACTIVITY CONSISTENCY
# =========================================================

def test_signal_and_activity_counts_match(
    db,
    company,
):

    DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result={
            "success": True,
            "title": (
                "Contract Management"
            ),
            "description": (
                "Legal technology and "
                "contract automation."
            ),
            "text": "",
            "final_url": (
                "https://example.com"
            ),
        },
    )

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(signals) == len(activities)

    assert len(signals) >= 1