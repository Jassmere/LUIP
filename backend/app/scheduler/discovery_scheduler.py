"""
LUIP Discovery Scheduler

Runs the LUIP Discovery Engine against active companies.

Version: 1.0.0
"""

from datetime import datetime, UTC

from app.db.session import SessionLocal
from app.models.company import Company
from app.discovery.discovery_engine import DiscoveryEngine


def run_discovery(limit=None):
    """
    Run the Discovery Engine for active companies.

    Args:
        limit: Optional maximum number of companies to scan.

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
            .order_by(Company.id.asc())
        )

        if limit is not None:
            query = query.limit(limit)

        companies = query.all()

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
            "results": results,
        }

        print("")
        print("======================================")
        print("LUIP Discovery Run Complete")
        print("======================================")
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