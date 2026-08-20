import pytest

from app.database import (
    Company,
    BuyingIntentSignal,
    BuyingActivity,
    CompanyScore,
    NextBestAction,
)

from app.db.session import SessionLocal

from app.services.discovery_signal_bridge import (
    DiscoverySignalBridge,
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


@pytest.fixture
def company(db):
    test_company = Company(
        name="LUIP Discovery Intelligence Integration Test",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(test_company)
    db.commit()
    db.refresh(test_company)

    yield test_company

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------

    db.query(NextBestAction).filter(
        NextBestAction.company_id == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(CompanyScore).filter(
        CompanyScore.company_id == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(BuyingActivity).filter(
        BuyingActivity.company_id == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(BuyingIntentSignal).filter(
        BuyingIntentSignal.company_id == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(Company).filter(
        Company.id == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.commit()


# =============================================================
# WEBSITE DISCOVERY → BUYING INTELLIGENCE
# =============================================================


def test_website_discovery_creates_buying_signal(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "title": "Enterprise Contract Management Platform",
        "description": (
            "We provide contract management and "
            "contract lifecycle automation."
        ),
        "text": (
            "Our legal technology platform provides "
            "contract management, legal operations and "
            "contract automation."
        ),
        "final_url": "https://example.com",
        "normalized_url": "https://example.com",
    }

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    assert result["signals_created"] > 0

    assert len(result["signals"]) > 0


# =============================================================
# VERIFY WEBSITE SIGNAL STORED
# =============================================================


def test_website_discovery_signal_is_stored(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "title": "Contract Management",
        "description": (
            "Enterprise contract management platform."
        ),
        "text": (
            "Contract management and contract automation."
        ),
        "final_url": "https://example.com",
    }

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert signal.signal_category == (
        "Website Intelligence"
    )

    assert signal.source == "Website Scanner"

    assert signal.score > 0

    assert signal.confidence == 80.0


# =============================================================
# VERIFY BUYING ACTIVITY
# =============================================================


def test_website_discovery_creates_buying_activity(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "title": "Contract Lifecycle Management",
        "description": (
            "Contract lifecycle management software."
        ),
        "text": (
            "Contract lifecycle management."
        ),
        "final_url": "https://example.com",
    }

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    activity = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .first()
    )

    assert activity is not None

    assert activity.activity_type == (
        "Website Intelligence"
    )

    assert activity.activity_source == (
        "Website Scanner"
    )

    assert activity.buying_score > 0

    assert activity.confidence == 80.0

    assert activity.processed is False


# =============================================================
# VERIFY COMPANY SCORE
# =============================================================


def test_discovery_updates_company_score(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "title": "Contract Automation",
        "description": (
            "Contract automation for legal teams."
        ),
        "text": (
            "Contract automation and legal automation."
        ),
        "final_url": "https://example.com",
    }

    DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    score = (
        db.query(CompanyScore)
        .filter(
            CompanyScore.company_id
            == company.id
        )
        .first()
    )

    assert score is not None

    assert score.buying_intent_score > 0

    assert score.confidence > 0

    assert score.priority in (
        "Low",
        "Medium",
        "High",
    )


# =============================================================
# VERIFY NEXT BEST ACTION
# =============================================================


def test_discovery_creates_next_best_action(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "title": "Legal Technology",
        "description": (
            "Legal technology and contract management."
        ),
        "text": (
            "Legal technology, contract management "
            "and legal operations."
        ),
        "final_url": "https://example.com",
    }

    DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    action = (
        db.query(NextBestAction)
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .first()
    )

    assert action is not None

    assert action.status == "Pending"

    assert action.priority in (
        "Low",
        "Medium",
        "High",
        "Critical",
    )

    assert action.action_type is not None


# =============================================================
# LINKEDIN DISCOVERY → BUYING INTELLIGENCE
# =============================================================


def test_linkedin_discovery_creates_buying_signal(
    db,
    company,
):

    discovery_result = {
        "success": True,
        "provider": "Test LinkedIn Provider",
        "linkedin_url": (
            "https://linkedin.com/company/example"
        ),
        "profile": {
            "about": (
                "Enterprise legal technology company."
            ),
            "departments": {
                "legal": "Legal Operations"
            },
            "roles": [
                "Contract Manager"
            ],
        },
    }

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    assert result["signals_created"] > 0

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert signal.signal_category == (
        "LinkedIn Intelligence"
    )

    assert signal.source == (
        "Test LinkedIn Provider"
    )

    assert signal.score > 0

    assert signal.confidence == 75.0


# =============================================================
# COMBINED DISCOVERY PIPELINE
# =============================================================


def test_combined_discovery_pipeline(
    db,
    company,
):

    website_result = {
        "success": True,
        "title": "Contract Management Platform",
        "description": (
            "Contract lifecycle management "
            "for enterprise legal teams."
        ),
        "text": (
            "Contract management, legal operations "
            "and contract automation."
        ),
        "final_url": "https://example.com",
    }

    linkedin_result = {
        "success": True,
        "provider": "Test LinkedIn Provider",
        "linkedin_url": (
            "https://linkedin.com/company/example"
        ),
        "profile": {
            "about": "Legal technology company",
            "departments": {
                "legal": "Legal Operations"
            },
            "roles": [
                "Contract Manager",
            ],
        },
    }

    result = DiscoverySignalBridge.process_discovery(
        db=db,
        company=company,
        website_result=website_result,
        linkedin_result=linkedin_result,
    )

    assert result["success"] is True

    assert result["company_id"] == company.id

    assert result["company"] == company.name

    assert result["signals_created"] > 0

    assert result["website"] is not None

    assert result["linkedin"] is not None

    # ---------------------------------------------------------
    # VERIFY DATABASE PIPELINE
    # ---------------------------------------------------------

    signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    assert len(signals) > 0

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(activities) > 0

    score = (
        db.query(CompanyScore)
        .filter(
            CompanyScore.company_id
            == company.id
        )
        .first()
    )

    assert score is not None

    assert score.buying_intent_score > 0

    action = (
        db.query(NextBestAction)
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .first()
    )

    assert action is not None

    assert action.status == "Pending"


# =============================================================
# NEGATIVE / CONSERVATIVE BEHAVIOUR
# =============================================================


def test_unsuccessful_website_scan_creates_no_signal(
    db,
    company,
):

    discovery_result = {
        "success": False,
    }

    result = DiscoverySignalBridge.website_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []


def test_empty_website_result_creates_no_signal(
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


def test_unsuccessful_linkedin_scan_creates_no_signal(
    db,
    company,
):

    discovery_result = {
        "success": False,
    }

    result = DiscoverySignalBridge.linkedin_signals(
        db=db,
        company=company,
        discovery_result=discovery_result,
    )

    assert result["success"] is True

    assert result["signals_created"] == 0

    assert result["signals"] == []