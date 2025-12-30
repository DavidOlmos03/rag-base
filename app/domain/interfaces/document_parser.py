"""
Abstract interface for document parsers.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ParsedDocument(BaseModel):
    """Parsed document structure."""

    content: str
    metadata: dict[str, str | int | float]
    num_pages: int | None = None
    file_type: str
    file_size: int


class DocumentParser(ABC):
    """Abstract interface for document parsers."""

    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document and extract text.

        Args:
            file_path: Path to the document file

        Returns:
            Parsed document with content and metadata
        """
        pass

    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports file format.

        Args:
            file_extension: File extension (e.g., '.pdf')

        Returns:
            True if format is supported
        """
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns:
            List of supported extensions
        """
        pass
