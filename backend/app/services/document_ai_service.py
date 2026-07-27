import re


class DocumentAIService:
    """
    Initial AI service.

    This version creates a simple summary.

    Future versions will include:
    - LLM integration
    - Clause extraction
    - Risk analysis
    - Semantic search
    """

    @staticmethod
    def generate_summary(text: str) -> str:

        if not text:
            return "No text could be extracted."

        cleaned = re.sub(r"\s+", " ", text).strip()

        words = cleaned.split()

        if len(words) <= 120:
            return cleaned

        return " ".join(words[:120]) + "..."