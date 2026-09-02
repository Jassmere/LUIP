"""
LUIP
Vega AI

Document AI Service

Responsibilities

• Generate executive summaries
• Produce document statistics
• Extract key legal information
• Build dashboard metadata
"""

import re


class DocumentAIService:

    MAX_SUMMARY_LENGTH = 1800

    @staticmethod
    def generate_summary(text: str):

        if not text:
            return "No document text extracted."

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) <= DocumentAIService.MAX_SUMMARY_LENGTH:
            return text

        return (
            text[: DocumentAIService.MAX_SUMMARY_LENGTH]
            + "..."
        )

    @staticmethod
    def word_count(text: str):

        if not text:
            return 0

        return len(text.split())

    @staticmethod
    def paragraph_count(text: str):

        if not text:
            return 0

        paragraphs = [
            p
            for p in text.split("\n")
            if p.strip()
        ]

        return len(paragraphs)

    @staticmethod
    def page_estimate(text: str):

        if not text:
            return 0

        words = len(text.split())

        return max(1, round(words / 450))

    @staticmethod
    def extract_statistics(text: str):

        return {

            "word_count":
                DocumentAIService.word_count(text),

            "paragraphs":
                DocumentAIService.paragraph_count(text),

            "estimated_pages":
                DocumentAIService.page_estimate(text),

        }

    @staticmethod
    def executive_summary(text: str):

        summary = DocumentAIService.generate_summary(text)

        stats = DocumentAIService.extract_statistics(text)

        return {

            "summary": summary,

            "statistics": stats

        }