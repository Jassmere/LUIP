from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from app.db.session import SessionLocal
from app.models.company import Company
from app.services.discovery_service import DiscoveryService


WORKBOOK_PATH = Path(
    r"C:\Users\jassm\OneDrive\LUIP-200-company-pilot-enrichment-v1-20260910.xlsx"
)

EXPECTED_COUNT = 200
EXPECTED_SHEET = "200 Company Pilot"
SOURCE = "LUIP-200-company-pilot-enrichment-v1-20260910.xlsx"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def column_number(cell_reference):
    letters = "".join(
        character
        for character in cell_reference
        if character.isalpha()
    )

    number = 0

    for character in letters:
        number = number * 26 + (ord(character.upper()) - ord("A") + 1)

    return number


def read_shared_strings(zip_file):
    try:
        xml = zip_file.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml)
    values = []

    for string_item in root.findall("main:si", NS):
        text_parts = []

        for text_node in string_item.iter(
            f"{{{NS['main']}}}t"
        ):
            text_parts.append(text_node.text or "")

        values.append("".join(text_parts))

    return values


def read_workbook_sheet_names(zip_file):
    workbook_root = ET.fromstring(
        zip_file.read("xl/workbook.xml")
    )

    relationships_root = ET.fromstring(
        zip_file.read("xl/_rels/workbook.xml.rels")
    )

    relationship_targets = {}

    for relationship in relationships_root:
        relationship_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")

        if relationship_id and target:
            if target.startswith("/"):
                target = target.lstrip("/")
            elif not target.startswith("xl/"):
                target = f"xl/{target}"

            relationship_targets[relationship_id] = target

    sheets = []

    sheets_root = workbook_root.find(
        "main:sheets",
        NS,
    )

    if sheets_root is None:
        return sheets

    for sheet in sheets_root:
        name = sheet.attrib.get("name")
        relationship_id = sheet.attrib.get(
            f"{{{NS['rel']}}}id"
        )

        target = relationship_targets.get(relationship_id)

        if name and target:
            sheets.append(
                {
                    "name": name,
                    "target": target,
                }
            )

    return sheets


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", NS)

    if cell_type == "inlineStr":
        text_parts = []

        for text_node in cell.iter(
            f"{{{NS['main']}}}t"
        ):
            text_parts.append(text_node.text or "")

        return "".join(text_parts)

    if value_node is None:
        return ""

    value = value_node.text or ""

    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return ""

    return value


def read_sheet_rows(zip_file, sheet_target):
    shared_strings = read_shared_strings(zip_file)

    root = ET.fromstring(
        zip_file.read(sheet_target)
    )

    rows = []

    sheet_data = root.find(
        "main:sheetData",
        NS,
    )

    if sheet_data is None:
        return rows

    for row in sheet_data.findall("main:row", NS):
        values = {}

        for cell in row.findall("main:c", NS):
            reference = cell.attrib.get("r")

            if not reference:
                continue

            column = column_number(reference)

            values[column] = cell_value(
                cell,
                shared_strings,
            )

        rows.append(values)

    return rows


def load_pilot_rows():
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(
            f"Workbook not found: {WORKBOOK_PATH}"
        )

    with ZipFile(WORKBOOK_PATH, "r") as zip_file:
        sheets = read_workbook_sheet_names(zip_file)

        sheet = next(
            (
                item
                for item in sheets
                if item["name"] == EXPECTED_SHEET
            ),
            None,
        )

        if sheet is None:
            available = ", ".join(
                item["name"]
                for item in sheets
            )

            raise ValueError(
                f"Expected sheet '{EXPECTED_SHEET}' "
                f"not found. Available sheets: {available}"
            )

        rows = read_sheet_rows(
            zip_file,
            sheet["target"],
        )

    if not rows:
        raise ValueError("Pilot worksheet is empty.")

    headers = {
        value.strip(): column
        for column, value in rows[0].items()
        if isinstance(value, str) and value.strip()
    }

    required_headers = {
        "Pilot ID",
        "Company",
        "Sector",
        "Decision Maker",
        "Title",
        "Business Email",
        "Email Verification",
        "Source / Evidence",
        "Outreach Status",
        "Notes",
    }

    missing_headers = sorted(
        required_headers - set(headers)
    )

    if missing_headers:
        raise ValueError(
            "Missing required workbook columns: "
            + ", ".join(missing_headers)
        )

    pilot_rows = []

    for row in rows[1:]:
        pilot_id_value = row.get(
            headers["Pilot ID"],
            "",
        )

        company_name = str(
            row.get(
                headers["Company"],
                "",
            )
        ).strip()

        if not str(pilot_id_value).strip() and not company_name:
            continue

        try:
            pilot_id = int(
                float(
                    str(pilot_id_value).strip()
                )
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid Pilot ID: {pilot_id_value}"
            ) from exc

        sector = str(
            row.get(
                headers["Sector"],
                "",
            )
        ).strip()

        pilot_rows.append(
            {
                "pilot_id": pilot_id,
                "company": company_name,
                "sector": sector,
                "decision_maker": str(
                    row.get(
                        headers["Decision Maker"],
                        "",
                    )
                ).strip(),
                "title": str(
                    row.get(
                        headers["Title"],
                        "",
                    )
                ).strip(),
                "business_email": str(
                    row.get(
                        headers["Business Email"],
                        "",
                    )
                ).strip(),
                "email_verification": str(
                    row.get(
                        headers["Email Verification"],
                        "",
                    )
                ).strip(),
                "source_evidence": str(
                    row.get(
                        headers["Source / Evidence"],
                        "",
                    )
                ).strip(),
                "outreach_status": str(
                    row.get(
                        headers["Outreach Status"],
                        "",
                    )
                ).strip(),
                "notes": str(
                    row.get(
                        headers["Notes"],
                        "",
                    )
                ).strip(),
            }
        )

    if len(pilot_rows) != EXPECTED_COUNT:
        raise ValueError(
            f"Expected exactly {EXPECTED_COUNT} pilot companies; "
            f"found {len(pilot_rows)}."
        )

    pilot_ids = [
        row["pilot_id"]
        for row in pilot_rows
    ]

    expected_ids = list(
        range(
            1,
            EXPECTED_COUNT + 1,
        )
    )

    if sorted(pilot_ids) != expected_ids:
        raise ValueError(
            "Pilot IDs are not exactly 1 through 200."
        )

    for row in pilot_rows:
        if not row["company"]:
            raise ValueError(
                f"Pilot ID {row['pilot_id']} has no company name."
            )

    return pilot_rows


def run_import(dry_run=True):
    pilot_rows = load_pilot_rows()

    db = SessionLocal()

    created = 0
    existing = 0

    try:
        print("")
        print("======================================")
        print("LUIP 200-Company Pilot Import")
        print("======================================")
        print(f"Workbook : {WORKBOOK_PATH}")
        print(f"Rows     : {len(pilot_rows)}")
        print(f"Mode     : {'DRY RUN' if dry_run else 'IMPORT'}")
        print("")

        for row in pilot_rows:
            company = (
                db.query(Company)
                .filter(
                    Company.name == row["company"]
                )
                .first()
            )

            if company:
                existing += 1
                status = "EXISTS"
            else:
                created += 1
                status = "WOULD CREATE"

                if not dry_run:
                    DiscoveryService.discover_company(
                        db=db,
                        name=row["company"],
                        industry=row["sector"] or None,
                        source=SOURCE,
                    )

            print(
                f"{row['pilot_id']:03d} | "
                f"{status:<11} | "
                f"{row['company']}"
            )

        if not dry_run:
            db.commit()

        print("")
        print("======================================")
        print("IMPORT SUMMARY")
        print("======================================")
        print(f"Pilot rows : {len(pilot_rows)}")
        print(f"Existing   : {existing}")
        print(f"Created    : {created}")
        print(f"Mode       : {'DRY RUN' if dry_run else 'IMPORT'}")
        print("")

        return {
            "success": True,
            "pilot_rows": len(pilot_rows),
            "existing": existing,
            "created": created,
            "dry_run": dry_run,
            "timestamp": datetime.now(UTC),
        }

    finally:
        db.close()


if __name__ == "__main__":
    run_import(dry_run=True)
