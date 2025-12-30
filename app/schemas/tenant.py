"""
Pydantic schemas for Tenant resources.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TenantBase(BaseModel):
    """Base tenant schema."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    is_active: bool = True


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""

    password: str = Field(..., min_length=8, max_length=100)


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    is_active: bool | None = None


class TenantInDB(TenantBase):
    """Schema for tenant in database."""

    id: UUID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantResponse(TenantBase):
    """Schema for tenant response (without password)."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantLogin(BaseModel):
    """Schema for tenant login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # Subject (tenant ID)
    exp: int  # Expiration
    iat: int  # Issued at
    type: str  # Token type (access/refresh)
