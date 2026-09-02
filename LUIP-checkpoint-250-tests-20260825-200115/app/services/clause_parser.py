import re

HEADING_PATTERN = re.compile(
    r"^(?:[A-Z][A-Za-z0-9\s,&()/-]{2,80})$",
    re.MULTILINE,
)

def parse_clauses(text: str):
    matches = list(HEADING_PATTERN.finditer(text))

    if not matches:
        return [{
            "heading": "Introduction",
            "content": text.strip()
        }]

    clauses = []

    for i, match in enumerate(matches):
        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        heading = match.group().strip()
        content = text[start:end].strip()

        if len(content) > 30:
            clauses.append({
                "heading": heading,
                "content": content
            })

    return clauses