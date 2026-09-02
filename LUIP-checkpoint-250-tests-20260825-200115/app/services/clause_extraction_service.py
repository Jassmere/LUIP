import re


class ClauseExtractionService:
    """
    LUIP Clause Extraction Engine V2

    Detects:
    - Numbered headings (1. Heading)
    - Roman numeral headings (I. Heading)
    - SECTION headings
    - ARTICLE headings
    - Common legal clause names
    """

    CLAUSE_KEYWORDS = [

        "Definitions",
        "Term",
        "Termination",
        "Confidentiality",
        "Confidential Information",
        "Payment",
        "Fees",
        "Liability",
        "Limitation of Liability",
        "Indemnity",
        "Warranty",
        "Force Majeure",
        "Dispute Resolution",
        "Arbitration",
        "Jurisdiction",
        "Intellectual Property",
        "Data Protection",
        "Privacy",
        "Governing Law",
        "Assignment",
        "Entire Agreement",
        "Notice",
        "Notices",
        "Relationship Of Parties",
        "No License",
        "Execution",
        "Signatures",
        "Conflicts",
        "Injunctive Relief",
        "Provisions Separable"

    ]

    @staticmethod
    def is_heading(line: str) -> bool:

        line = line.strip()

        if not line:
            return False

        # SECTION 5

        if re.match(r"^SECTION\s+\d+", line, re.IGNORECASE):
            return True

        # ARTICLE III

        if re.match(r"^ARTICLE\s+[IVXLCDM]+", line, re.IGNORECASE):
            return True

        # 1. Heading

        if re.match(r"^\d+\.\s*", line):
            return True

        # 10. Heading

        if re.match(r"^\d+\s*\.", line):
            return True

        # I. Heading

        if re.match(r"^[IVXLCDM]+\.", line):
            return True

        # A. Heading

        if re.match(r"^[A-Z]\.", line):
            return True

        # Common legal headings

        for keyword in ClauseExtractionService.CLAUSE_KEYWORDS:

            if keyword.lower() in line.lower():
                return True

        return False

    @staticmethod
    def clean_heading(line: str) -> str:
        """
        Removes numbering from headings.

        Example:

        1. Term of Agreement
            ->
        Term of Agreement
        """

        line = re.sub(r"^\d+\.\s*", "", line)
        line = re.sub(r"^[IVXLCDM]+\.\s*", "", line, flags=re.IGNORECASE)
        line = re.sub(r"^[A-Z]\.\s*", "", line)

        return line.strip()

    @staticmethod
    def extract(text: str):

        clauses = []

        current_heading = "Introduction"

        current_content = []

        lines = text.splitlines()

        for raw_line in lines:

            line = raw_line.strip()

            if not line:
                continue

            if ClauseExtractionService.is_heading(line):

                if current_content:

                    clauses.append({

                        "heading": current_heading,

                        "content": "\n".join(current_content),

                        "clause_type": current_heading,

                        "confidence_score": 95

                    })

                current_heading = ClauseExtractionService.clean_heading(line)

                current_content = []

            else:

                current_content.append(line)

        if current_content:

            clauses.append({

                "heading": current_heading,

                "content": "\n".join(current_content),

                "clause_type": current_heading,

                "confidence_score": 95

            })

        return clauses