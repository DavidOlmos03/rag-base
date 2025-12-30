"""
Authentication endpoints.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_tenant_repository
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.infrastructure.database.models import Tenant
from app.infrastructure.database.repositories.tenant_repo import TenantRepository
from app.schemas.tenant import TenantCreate, TenantLogin, TenantResponse, TokenResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def register(
    tenant_data: TenantCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """Register a new tenant/user.

    Args:
        tenant_data: Tenant registration data
        tenant_repo: Tenant repository

    Returns:
        Created tenant

    Raises:
        HTTPException: If email already exists
    """
    try:
        # Hash password
        hashed_password = get_password_hash(tenant_data.password)

        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            email=tenant_data.email,
            hashed_password=hashed_password,
            is_active=True,
        )

        created_tenant = await tenant_repo.create(tenant)

        logger.info("user_registered", tenant_id=str(created_tenant.id), email=created_tenant.email)

        return created_tenant

    except Exception as e:
        logger.error("registration_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: TenantLogin,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """Login and get access tokens.

    Args:
        credentials: Login credentials
        tenant_repo: Tenant repository

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get tenant by email
    tenant = await tenant_repo.get_by_email(credentials.email)

    if not tenant:
        logger.warning("login_failed", email=credentials.email, reason="user_not_found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(credentials.password, tenant.hashed_password):
        logger.warning("login_failed", email=credentials.email, reason="invalid_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is active
    if not tenant.is_active:
        logger.warning("login_failed", email=credentials.email, reason="account_inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        subject=str(tenant.id),
        additional_claims={"email": tenant.email},
    )

    refresh_token = create_refresh_token(subject=str(tenant.id))

    logger.info("user_logged_in", tenant_id=str(tenant.id), email=tenant.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
):
    """Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token
        tenant_repo: Tenant repository

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    from app.core.security import decode_token
    from uuid import UUID

    try:
        # Decode refresh token
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Get tenant
        tenant_id = UUID(payload.get("sub"))
        tenant = await tenant_repo.get_by_id(tenant_id)

        if not tenant or not tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Create new tokens
        access_token = create_access_token(
            subject=str(tenant.id),
            additional_claims={"email": tenant.email},
        )

        new_refresh_token = create_refresh_token(subject=str(tenant.id))

        logger.info("token_refreshed", tenant_id=str(tenant.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    except Exception as e:
        logger.warning("token_refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
