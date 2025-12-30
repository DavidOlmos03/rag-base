"""
Custom exceptions for RAG Base Service.
"""

from typing import Any


class RAGBaseException(Exception):
    """Base exception for all RAG service errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization
class AuthenticationError(RAGBaseException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(RAGBaseException):
    """Raised when user lacks permission."""

    pass


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    pass


# Resource Errors
class ResourceNotFoundError(RAGBaseException):
    """Raised when a requested resource is not found."""

    pass


class ResourceAlreadyExistsError(RAGBaseException):
    """Raised when attempting to create a resource that already exists."""

    pass


class ResourceConflictError(RAGBaseException):
    """Raised when a resource conflict occurs."""

    pass


# Document Processing
class DocumentProcessingError(RAGBaseException):
    """Raised when document processing fails."""

    pass


class UnsupportedFileFormatError(DocumentProcessingError):
    """Raised when file format is not supported."""

    pass


class FileTooLargeError(DocumentProcessingError):
    """Raised when file exceeds size limit."""

    pass


class DocumentParsingError(DocumentProcessingError):
    """Raised when document parsing fails."""

    pass


# Embedding Errors
class EmbeddingError(RAGBaseException):
    """Raised when embedding generation fails."""

    pass


class EmbeddingModelNotFoundError(EmbeddingError):
    """Raised when embedding model is not available."""

    pass


# Vector Store Errors
class VectorStoreError(RAGBaseException):
    """Raised when vector store operation fails."""

    pass


class CollectionNotFoundError(VectorStoreError):
    """Raised when vector collection is not found."""

    pass


class VectorSearchError(VectorStoreError):
    """Raised when vector search fails."""

    pass


# LLM Errors
class LLMError(RAGBaseException):
    """Raised when LLM operation fails."""

    pass


class LLMProviderError(LLMError):
    """Raised when LLM provider is unavailable."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class InvalidLLMConfigError(LLMError):
    """Raised when LLM configuration is invalid."""

    pass


# RAG Pipeline Errors
class RAGPipelineError(RAGBaseException):
    """Raised when RAG pipeline fails."""

    pass


class RetrievalError(RAGPipelineError):
    """Raised when retrieval step fails."""

    pass


class GenerationError(RAGPipelineError):
    """Raised when generation step fails."""

    pass


# Validation Errors
class ValidationError(RAGBaseException):
    """Raised when validation fails."""

    pass


class InvalidInputError(ValidationError):
    """Raised when input is invalid."""

    pass


# Rate Limiting
class RateLimitExceededError(RAGBaseException):
    """Raised when rate limit is exceeded."""

    pass


# Cache Errors
class CacheError(RAGBaseException):
    """Raised when cache operation fails."""

    pass


# Database Errors
class DatabaseError(RAGBaseException):
    """Raised when database operation fails."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    pass


# Configuration Errors
class ConfigurationError(RAGBaseException):
    """Raised when configuration is invalid."""

    pass


# External Service Errors
class ExternalServiceError(RAGBaseException):
    """Raised when external service call fails."""

    pass


class ExternalServiceTimeoutError(ExternalServiceError):
    """Raised when external service times out."""

    pass


class ExternalServiceUnavailableError(ExternalServiceError):
    """Raised when external service is unavailable."""

    pass
