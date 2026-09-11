"""
LUIP Discovery Scheduler

Runs the LUIP Discovery Engine against active companies.

Version: 1.1.0
"""

from datetime import datetime, UTC

from app.db.session import SessionLocal
from app.models.company import Company
from app.discovery.discovery_engine import DiscoveryEngine


PILOT_SOURCE = "LUIP-200-company-pilot-enrichment-v1-20260910.xlsx"


def run_discovery(limit=None, pilot_only=False):
    """
    Run the Discovery Engine for active companies.

    Args:
        limit: Optional maximum number of companies to scan.
        pilot_only: When True, scan only the 200-company LUIP pilot.

    Returns:
        Structured summary of the discovery run.
    """

    db = SessionLocal()

    started_at = datetime.now(UTC)

    results = []

    scanned = 0
    completed = 0
    failed = 0

    print("")
    print("======================================")
    print("LUIP Discovery Engine")
    print("======================================")
    print(f"[{started_at}] Discovery run started.")

    try:
        query = (
            db.query(Company)
            .filter(Company.active.is_(True))
        )

        if pilot_only:
            query = query.filter(
                Company.discovered_from == PILOT_SOURCE
            )

        query = query.order_by(Company.id.asc())

        if limit is not None:
            query = query.limit(limit)

        companies = query.all()

        selection_label = (
            "200-company pilot"
            if pilot_only
            else "all active companies"
        )

        print(
            f"[{datetime.now(UTC)}] "
            f"Discovery scope: {selection_label}"
        )

        print(
            f"[{datetime.now(UTC)}] "
            f"Active companies selected: {len(companies)}"
        )

        for company in companies:
            scanned += 1

            print("")
            print("--------------------------------------")
            print(
                f"Scanning company {scanned}/{len(companies)}: "
                f"{company.name}"
            )
            print("--------------------------------------")

            try:
                result = DiscoveryEngine.scan_company(
                    db=db,
                    company=company,
                    linkedin_url=company.linkedin_url,
                )

                completed += 1

                results.append(
                    {
                        "company_id": company.id,
                        "company_name": company.name,
                        "status": "Completed",
                        "result": result,
                    }
                )

                print(
                    f"[{datetime.now(UTC)}] "
                    f"Completed: {company.name}"
                )

            except Exception as exc:
                failed += 1

                results.append(
                    {
                        "company_id": company.id,
                        "company_name": company.name,
                        "status": "Failed",
                        "error": str(exc),
                    }
                )

                print(
                    f"[{datetime.now(UTC)}] "
                    f"Failed: {company.name}"
                )
                print(f"Error: {exc}")

        finished_at = datetime.now(UTC)

        summary = {
            "success": failed == 0,
            "started_at": started_at,
            "finished_at": finished_at,
            "selected": len(companies),
            "scanned": scanned,
            "completed": completed,
            "failed": failed,
            "pilot_only": pilot_only,
            "results": results,
        }

        print("")
        print("======================================")
        print("LUIP Discovery Run Complete")
        print("======================================")
        print(f"Scope    : {selection_label}")
        print(f"Selected : {len(companies)}")
        print(f"Scanned  : {scanned}")
        print(f"Completed: {completed}")
        print(f"Failed   : {failed}")
        print(f"Finished : {finished_at}")
        print("")

        return summary

    finally:
        db.close()


if __name__ == "__main__":
    run_discovery()
