from pathlib import Path

import docx
from PyPDF2 import PdfReader


class TextExtractionService:
    """
    Extract text from supported document types.
    """

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Automatically determine the file type and extract text.
        """

        suffix = Path(file_path).suffix.lower()

        if suffix == ".pdf":
            return TextExtractionService.extract_pdf(file_path)

        if suffix == ".docx":
            return TextExtractionService.extract_docx(file_path)

        return ""

    @staticmethod
    def extract_pdf(file_path: str) -> str:

        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages)

    @staticmethod
    def extract_docx(file_path: str) -> str:

        document = docx.Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:

            if paragraph.text:

                paragraphs.append(paragraph.text)

        return "\n".join(paragraphs)