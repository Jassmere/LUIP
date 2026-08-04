CLAUSE_TYPES = {
    "Confidentiality": [
        "confidential",
        "non-disclosure",
        "nda"
    ],

    "Termination": [
        "terminate",
        "termination"
    ],

    "Liability": [
        "liability",
        "indemnity"
    ],

    "Payment": [
        "payment",
        "invoice",
        "fees"
    ],

    "Intellectual Property": [
        "intellectual property",
        "copyright",
        "trademark"
    ],

    "Data Protection": [
        "popia",
        "gdpr",
        "privacy"
    ]
}


def classify_clause(text):
    lower = text.lower()

    for clause_type, keywords in CLAUSE_TYPES.items():
        if any(word in lower for word in keywords):
            return clause_type

    return "General"