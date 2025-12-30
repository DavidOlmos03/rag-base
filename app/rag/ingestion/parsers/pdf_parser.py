"""
PDF document parser implementation.
"""

import os
from pathlib import Path

import fitz  # PyMuPDF

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger
from app.domain.interfaces.document_parser import DocumentParser, ParsedDocument

logger = get_logger(__name__)


class PDFParser(DocumentParser):
    """PDF parser using PyMuPDF."""

    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse a PDF document and extract text.

        Args:
            file_path: Path to the PDF file

        Returns:
            Parsed document with content and metadata

        Raises:
            DocumentParsingError: If parsing fails
        """
        try:
            doc = fitz.open(file_path)

            # Extract text from all pages
            text_content = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_content.append(text)

            full_content = "\n\n".join(text_content)

            # Extract metadata
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
            }

            # Get file stats
            file_size = os.path.getsize(file_path)
            num_pages = len(doc)

            doc.close()

            logger.info(
                "pdf_parsed",
                file_path=file_path,
                num_pages=num_pages,
                content_length=len(full_content),
            )

            return ParsedDocument(
                content=full_content,
                metadata=metadata,
                num_pages=num_pages,
                file_type="pdf",
                file_size=file_size,
            )

        except Exception as e:
            logger.error("pdf_parsing_failed", file_path=file_path, error=str(e))
            raise DocumentParsingError(f"Failed to parse PDF: {str(e)}") from e

    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports file format.

        Args:
            file_extension: File extension (e.g., '.pdf')

        Returns:
            True if format is supported
        """
        return file_extension.lower() in self.supported_formats

    @property
    def supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns:
            List of supported extensions
        """
        return [".pdf"]
