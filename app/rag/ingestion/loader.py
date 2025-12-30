"""
Document loader with parser factory.
"""

from pathlib import Path

from app.core.exceptions import UnsupportedFileFormatError
from app.core.logging import get_logger
from app.domain.interfaces.document_parser import DocumentParser, ParsedDocument
from app.rag.ingestion.parsers.docx_parser import DOCXParser
from app.rag.ingestion.parsers.pdf_parser import PDFParser
from app.rag.ingestion.parsers.txt_parser import TXTParser

logger = get_logger(__name__)


class DocumentLoader:
    """Document loader with automatic parser selection."""

    def __init__(self) -> None:
        """Initialize document loader with available parsers."""
        self.parsers: dict[str, DocumentParser] = {
            ".pdf": PDFParser(),
            ".docx": DOCXParser(),
            ".doc": DOCXParser(),
            ".txt": TXTParser(),
            ".md": TXTParser(),
            ".markdown": TXTParser(),
        }

    async def load(self, file_path: str) -> ParsedDocument:
        """Load and parse a document.

        Args:
            file_path: Path to the document file

        Returns:
            Parsed document

        Raises:
            UnsupportedFileFormatError: If file format is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.parsers:
            supported = ", ".join(self.parsers.keys())
            raise UnsupportedFileFormatError(
                f"Unsupported file format: {extension}. Supported: {supported}"
            )

        parser = self.parsers[extension]
        logger.info("loading_document", file_path=file_path, parser=parser.__class__.__name__)

        return await parser.parse(file_path)

    def supports_format(self, file_extension: str) -> bool:
        """Check if file format is supported.

        Args:
            file_extension: File extension (e.g., '.pdf')

        Returns:
            True if format is supported
        """
        return file_extension.lower() in self.parsers

    def get_supported_formats(self) -> list[str]:
        """Get list of all supported file formats.

        Returns:
            List of supported extensions
        """
        return list(self.parsers.keys())
