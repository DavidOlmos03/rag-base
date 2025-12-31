"""
Core configuration settings for RAG Base Service.
Uses Pydantic Settings for environment variable management.
"""

from typing import List, Literal
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "RAG Base Service"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    SECRET_KEY: str = Field(..., min_length=32)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: RedisDsn
    REDIS_MAX_CONNECTIONS: int = 50

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_TIMEOUT: int = 30
    QDRANT_PREFER_GRPC: bool = False

    # LLM Providers (Optional - Can be configured per tenant)
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None
    OPENAI_DEFAULT_MODEL: str = "gpt-3.5-turbo"

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_DEFAULT_MODEL: str = "claude-3-sonnet-20240229"

    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_DEFAULT_MODEL: str = "deepseek-chat"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "phi3:mini"

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: Literal["cpu", "cuda", "mps"] = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_MAX_LENGTH: int = 512
    EMBEDDING_CACHE_TTL: int = 2592000  # 30 days

    # RAG Settings
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
    DEFAULT_TOP_K: int = 5
    DEFAULT_RETRIEVAL_SCORE_THRESHOLD: float = 0.7
    CONTEXT_MAX_TOKENS: int = 2000

    # Cache
    QUERY_CACHE_TTL: int = 3600  # 1 hour
    RESPONSE_CACHE_TTL: int = 1800  # 30 minutes

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Security
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx"]
    UPLOAD_DIR: str = "./uploads"

    # Observability
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # Cost Tracking
    BUDGET_MODE: Literal["minimal", "balanced", "premium"] = "balanced"
    ENABLE_COST_TRACKING: bool = True

    # Feature Flags
    ENABLE_RERANKING: bool = False
    ENABLE_HYBRID_SEARCH: bool = True
    ENABLE_QUERY_EXPANSION: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: str | List[str]) -> List[str]:
        """Parse allowed extensions from string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return str(self.DATABASE_URL).replace("+asyncpg", "+psycopg2")


# Global settings instance
settings = Settings()
