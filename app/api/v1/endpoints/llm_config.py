"""
LLM configuration endpoints.
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.llm.llm_factory import LLMFactory
from app.api.v1.dependencies import get_current_user, get_llm_config_repository
from app.core.logging import get_logger
from app.infrastructure.database.models import LLMConfig, Tenant
from app.infrastructure.database.repositories.llm_config_repo import LLMConfigRepository
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigUpdate,
    LLMProviderInfo,
    LLMTestRequest,
    LLMTestResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/providers", response_model=dict[str, LLMProviderInfo])
async def get_available_providers():
    """Get information about available LLM providers.

    Returns:
        Dictionary of provider information
    """
    providers = LLMFactory.get_available_providers()

    # Convert to Pydantic models
    response = {}
    for key, info in providers.items():
        response[key] = LLMProviderInfo(
            name=info["name"],
            display_name=info["name"],
            models=info["models"],
            requires_api_key=info["requires_api_key"],
            supports_streaming=info["supports_streaming"],
        )

    return response


@router.post("/config", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_config(
    config_data: LLMConfigCreate,
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Create a new LLM configuration.

    Args:
        config_data: LLM configuration data
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Returns:
        Created LLM configuration
    """
    # Validate provider and model
    providers = LLMFactory.get_available_providers()
    if config_data.provider not in providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {config_data.provider}",
        )

    # In production, encrypt the API key
    # For now, store as-is (INSECURE - fix in production)
    api_key_encrypted = config_data.api_key

    # Create config
    llm_config = LLMConfig(
        tenant_id=current_user.id,
        provider=config_data.provider,
        model=config_data.model,
        api_key_encrypted=api_key_encrypted,
        base_url=config_data.base_url,
        temperature=config_data.temperature,
        max_tokens=config_data.max_tokens,
        is_active=True,  # New config becomes active
    )

    created_config = await llm_config_repo.create(llm_config)

    logger.info(
        "llm_config_created",
        config_id=str(created_config.id),
        tenant_id=str(current_user.id),
        provider=created_config.provider,
    )

    return created_config


@router.get("/config", response_model=LLMConfigResponse)
async def get_active_llm_config(
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Get active LLM configuration for current user.

    Args:
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Returns:
        Active LLM configuration

    Raises:
        HTTPException: If no active configuration
    """
    config = await llm_config_repo.get_active_by_tenant(current_user.id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active LLM configuration found",
        )

    return config


@router.get("/config/all", response_model=list[LLMConfigResponse])
async def get_all_llm_configs(
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Get all LLM configurations for current user.

    Args:
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Returns:
        List of LLM configurations
    """
    configs = await llm_config_repo.get_all_by_tenant(current_user.id)
    return configs


@router.patch("/config/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: UUID,
    config_update: LLMConfigUpdate,
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Update an LLM configuration.

    Args:
        config_id: Configuration ID
        config_update: Configuration updates
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Returns:
        Updated configuration

    Raises:
        HTTPException: If config not found or unauthorized
    """
    # Get config
    config = await llm_config_repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    if config.tenant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this configuration",
        )

    # Update fields
    if config_update.provider is not None:
        config.provider = config_update.provider
    if config_update.model is not None:
        config.model = config_update.model
    if config_update.api_key is not None:
        config.api_key_encrypted = config_update.api_key  # Encrypt in production
    if config_update.base_url is not None:
        config.base_url = config_update.base_url
    if config_update.temperature is not None:
        config.temperature = config_update.temperature
    if config_update.max_tokens is not None:
        config.max_tokens = config_update.max_tokens

    updated_config = await llm_config_repo.update(config)

    logger.info("llm_config_updated", config_id=str(config_id))

    return updated_config


@router.post("/config/{config_id}/activate", response_model=LLMConfigResponse)
async def activate_llm_config(
    config_id: UUID,
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Activate an LLM configuration.

    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Returns:
        Activated configuration

    Raises:
        HTTPException: If config not found or unauthorized
    """
    # Get config
    config = await llm_config_repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    if config.tenant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate this configuration",
        )

    # Activate
    activated_config = await llm_config_repo.activate(config_id)

    logger.info("llm_config_activated", config_id=str(config_id))

    return activated_config


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: UUID,
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
):
    """Delete an LLM configuration.

    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        llm_config_repo: LLM config repository

    Raises:
        HTTPException: If config not found or unauthorized
    """
    # Get config
    config = await llm_config_repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    if config.tenant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this configuration",
        )

    # Delete
    await llm_config_repo.delete(config_id)

    logger.info("llm_config_deleted", config_id=str(config_id))


@router.post("/test", response_model=LLMTestResponse)
async def test_llm_connection(test_request: LLMTestRequest):
    """Test LLM connection and configuration.

    Args:
        test_request: Test request with LLM details

    Returns:
        Test result
    """
    start_time = time.time()

    try:
        # Create LLM client
        llm_client = LLMFactory.create_client(
            provider=test_request.provider,
            model=test_request.model,
            api_key=test_request.api_key,
            base_url=test_request.base_url,
        )

        # Test health check
        is_healthy = await llm_client.health_check()

        latency_ms = (time.time() - start_time) * 1000

        if is_healthy:
            return LLMTestResponse(
                success=True,
                message=f"Successfully connected to {test_request.provider}",
                latency_ms=latency_ms,
            )
        else:
            return LLMTestResponse(
                success=False,
                message=f"Failed to connect to {test_request.provider}",
                latency_ms=latency_ms,
            )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error("llm_test_failed", provider=test_request.provider, error=str(e))

        return LLMTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}",
            latency_ms=latency_ms,
        )
