"""
TXT document parser implementation.
"""

import os

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger
from app.domain.interfaces.document_parser import DocumentParser, ParsedDocument

logger = get_logger(__name__)


class TXTParser(DocumentParser):
    """Plain text parser."""

    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse a TXT document and extract text.

        Args:
            file_path: Path to the TXT file

        Returns:
            Parsed document with content and metadata

        Raises:
            DocumentParsingError: If parsing fails
        """
        try:
            # Try different encodings
            encodings = ["utf-8", "latin-1", "cp1252"]
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                raise DocumentParsingError("Could not decode text file with supported encodings")

            # Get file stats
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            # Estimate pages (assuming ~3000 chars per page)
            estimated_pages = max(1, len(content) // 3000)

            metadata = {
                "filename": file_name,
                "encoding": encoding,
            }

            logger.info(
                "txt_parsed",
                file_path=file_path,
                content_length=len(content),
                encoding=encoding,
            )

            return ParsedDocument(
                content=content,
                metadata=metadata,
                num_pages=estimated_pages,
                file_type="txt",
                file_size=file_size,
            )

        except Exception as e:
            logger.error("txt_parsing_failed", file_path=file_path, error=str(e))
            raise DocumentParsingError(f"Failed to parse TXT: {str(e)}") from e

    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports file format.

        Args:
            file_extension: File extension (e.g., '.txt')

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
        return [".txt", ".md", ".markdown"]
