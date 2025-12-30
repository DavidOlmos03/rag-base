"""
Pydantic schemas for LLM Configuration.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LLMProviderInfo(BaseModel):
    """Schema for LLM provider information."""

    name: str
    display_name: str
    models: list[str]
    requires_api_key: bool
    supports_streaming: bool


class LLMConfigBase(BaseModel):
    """Base LLM configuration schema."""

    provider: Literal["openai", "anthropic", "deepseek", "ollama"]
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4000)


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating LLM configuration."""

    api_key: str | None = None
    base_url: str | None = None
    tenant_id: UUID


class LLMConfigUpdate(BaseModel):
    """Schema for updating LLM configuration."""

    provider: Literal["openai", "anthropic", "deepseek", "ollama"] | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4000)


class LLMConfigInDB(LLMConfigBase):
    """Schema for LLM configuration in database."""

    id: UUID
    tenant_id: UUID
    api_key_encrypted: str | None = None
    base_url: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response (no API key)."""

    id: UUID
    base_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMTestRequest(BaseModel):
    """Schema for testing LLM connection."""

    provider: Literal["openai", "anthropic", "deepseek", "ollama"]
    model: str
    api_key: str | None = None
    base_url: str | None = None


class LLMTestResponse(BaseModel):
    """Schema for LLM test response."""

    success: bool
    message: str
    latency_ms: float | None = None
