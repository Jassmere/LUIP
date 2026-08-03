import re


class ClauseExtractionService:
    """
    Basic clause extraction engine.

    This is Version 1.

    Future versions will use AI and NLP.

    Current version detects common legal headings.
    """

    CLAUSE_PATTERNS = [

        "Definitions",

        "Term",

        "Termination",

        "Confidentiality",

        "Payment",

        "Fees",

        "Liability",

        "Indemnity",

        "Warranty",

        "Force Majeure",

        "Dispute Resolution",

        "Jurisdiction",

        "Intellectual Property",

        "Data Protection",

        "Privacy",

        "Governing Law",

        "Assignment",

        "Entire Agreement",

        "Notice",

    ]

    @staticmethod
    def extract(text: str):

        clauses = []

        current_heading = "Introduction"

        current_content = []

        lines = text.splitlines()

        for line in lines:

            clean = line.strip()

            if not clean:
                continue

            matched = False

            for pattern in ClauseExtractionService.CLAUSE_PATTERNS:

                if re.fullmatch(pattern, clean, re.IGNORECASE):

                    if current_content:

                        clauses.append({

                            "heading": current_heading,

                            "content": "\n".join(current_content),

                            "clause_type": current_heading,

                            "confidence_score": 100,

                        })

                    current_heading = clean

                    current_content = []

                    matched = True

                    break

            if not matched:

                current_content.append(clean)

        if current_content:

            clauses.append({

                "heading": current_heading,

                "content": "\n".join(current_content),

                "clause_type": current_heading,

                "confidence_score": 100,

            })

        return clauses