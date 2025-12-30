"""
Text chunking strategies for document processing.
"""

import re
from typing import Literal

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Text chunker with multiple strategies."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        strategy: Literal["fixed", "sentence", "paragraph"] = "fixed",
    ):
        """Initialize text chunker.

        Args:
            chunk_size: Size of chunks in characters
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy (fixed, sentence, paragraph)
        """
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
        self.strategy = strategy

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Chunk text into smaller pieces.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunks with metadata
        """
        if self.strategy == "fixed":
            chunks = self._chunk_fixed_size(text)
        elif self.strategy == "sentence":
            chunks = self._chunk_by_sentences(text)
        elif self.strategy == "paragraph":
            chunks = self._chunk_by_paragraphs(text)
        else:
            chunks = self._chunk_fixed_size(text)

        # Add metadata to chunks
        chunk_dicts = []
        for idx, chunk in enumerate(chunks):
            chunk_dict = {
                "content": chunk,
                "chunk_index": idx,
                "chunk_count": len(chunks),
                "metadata": metadata or {},
            }
            chunk_dicts.append(chunk_dict)

        logger.debug(
            "text_chunked",
            strategy=self.strategy,
            text_length=len(text),
            num_chunks=len(chunks),
        )

        return chunk_dicts

    def _chunk_fixed_size(self, text: str) -> list[str]:
        """Chunk text into fixed-size pieces with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at word boundary
            if end < len(text):
                # Find last space before chunk_size
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start <= 0 or start >= len(text):
                break

        return chunks

    def _chunk_by_sentences(self, text: str) -> list[str]:
        """Chunk text by sentences, respecting chunk_size.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split by sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_by_paragraphs(self, text: str) -> list[str]:
        """Chunk text by paragraphs, respecting chunk_size.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split by paragraph boundaries (double newline or more)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(current_chunk) + len(paragraph) <= self.chunk_size:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If single paragraph exceeds chunk_size, chunk it
                if len(paragraph) > self.chunk_size:
                    para_chunks = self._chunk_fixed_size(paragraph)
                    chunks.extend(para_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
