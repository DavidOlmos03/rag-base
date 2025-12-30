"""
RAG query endpoints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import (
    get_cache_service,
    get_current_user,
    get_embedding_provider_service,
    get_llm_config_repository,
    get_query_repository,
    get_vector_store_service,
)
from app.adapters.llm.llm_factory import LLMFactory
from app.core.exceptions import InvalidLLMConfigError
from app.core.logging import get_logger
from app.infrastructure.cache.cache_service import CacheService
from app.infrastructure.database.models import Query, Tenant
from app.infrastructure.database.repositories.llm_config_repo import LLMConfigRepository
from app.infrastructure.database.repositories.query_repo import QueryRepository
from app.rag.embeddings.batch_processor import EmbeddingBatchProcessor
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval.vector_retriever import VectorRetriever
from app.schemas.query import QueryHistoryResponse, QueryRequest, QueryResponse

logger = get_logger(__name__)

router = APIRouter()


async def get_rag_pipeline(
    current_user=Depends(get_current_user),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
    vector_store=Depends(get_vector_store_service),
    embedding_provider=Depends(get_embedding_provider_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> RAGPipeline:
    """Get RAG pipeline with user's LLM configuration.

    Returns:
        Configured RAG pipeline

    Raises:
        HTTPException: If LLM not configured
    """
    # Get active LLM config for user
    llm_config = await llm_config_repo.get_active_by_tenant(current_user.id)

    if not llm_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active LLM configuration. Please configure an LLM provider first.",
        )

    # Create LLM client
    try:
        # Decrypt API key if needed (simplified - in production use proper encryption)
        api_key = llm_config.api_key_encrypted

        llm_client = LLMFactory.create_client(
            provider=llm_config.provider,
            model=llm_config.model,
            api_key=api_key,
            base_url=llm_config.base_url,
        )
    except InvalidLLMConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create retriever
    embedding_processor = EmbeddingBatchProcessor(embedding_provider, cache_service)
    retriever = VectorRetriever(vector_store, embedding_provider)

    # Create RAG pipeline
    pipeline = RAGPipeline(
        retriever=retriever,
        llm_client=llm_client,
    )

    return pipeline


@router.post("/", response_model=QueryResponse)
async def query_rag(
    query_request: QueryRequest,
    current_user=Depends(get_current_user),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    llm_config_repo: LLMConfigRepository = Depends(get_llm_config_repository),
    query_repo: QueryRepository = Depends(get_query_repository),
):
    """Execute a RAG query.

    Args:
        query_request: Query request
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline
        llm_config_repo: LLM config repository
        query_repo: Query repository

    Returns:
        Query response with answer and contexts
    """
    logger.info(
        "rag_query_received",
        tenant_id=str(current_user.id),
        query_length=len(query_request.query),
    )

    try:
        # Execute RAG query
        result = await rag_pipeline.query(
            query=query_request.query,
            tenant_id=str(current_user.id),
            top_k=query_request.top_k,
            score_threshold=query_request.score_threshold,
            temperature=query_request.temperature,
            max_tokens=query_request.max_tokens,
            use_hybrid=query_request.use_hybrid_search,
        )

        # Save query to history
        query_record = Query(
            tenant_id=current_user.id,
            query_text=query_request.query,
            answer_text=result["answer"],
            model_used=result["model_used"],
            tokens_used=result["tokens_used"],
            processing_time=result["processing_time"],
            num_contexts=len(result["contexts"]),
        )

        await query_repo.create(query_record)

        # Build response
        response = QueryResponse(
            query_id=result["query_id"],
            query=result["query"],
            answer=result["answer"],
            contexts=[
                {
                    "content": ctx["content"],
                    "score": ctx["score"],
                    "document_id": UUID(ctx["document_id"]),
                    "chunk_id": ctx["chunk_id"],
                    "metadata": ctx["metadata"],
                }
                for ctx in result["contexts"]
            ],
            model_used=result["model_used"],
            tokens_used=result["tokens_used"],
            processing_time=result["processing_time"],
            created_at=datetime.utcnow(),
        )

        return response

    except Exception as e:
        logger.error("rag_query_failed", tenant_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/stream")
async def query_rag_stream(
    query_request: QueryRequest,
    current_user: Tenant = Depends(get_current_user),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """Execute a RAG query with streaming response.

    Args:
        query_request: Query request
        current_user: Current authenticated user
        rag_pipeline: RAG pipeline

    Returns:
        Streaming response
    """
    logger.info(
        "rag_query_stream_received",
        tenant_id=str(current_user.id),
        query_length=len(query_request.query),
    )

    async def generate():
        """Generate streaming response."""
        try:
            async for chunk in rag_pipeline.query_stream(
                query=query_request.query,
                tenant_id=str(current_user.id),
                top_k=query_request.top_k,
                score_threshold=query_request.score_threshold,
                temperature=query_request.temperature,
                max_tokens=query_request.max_tokens,
                use_hybrid=query_request.use_hybrid_search,
            ):
                yield chunk

        except Exception as e:
            logger.error("rag_query_stream_failed", error=str(e))
            yield f"\n\nError: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/history", response_model=QueryHistoryResponse)
async def get_query_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Tenant = Depends(get_current_user),
    query_repo: QueryRepository = Depends(get_query_repository),
):
    """Get query history for current user.

    Args:
        limit: Maximum number of queries
        offset: Pagination offset
        current_user: Current authenticated user
        query_repo: Query repository

    Returns:
        Query history
    """
    queries = await query_repo.get_by_tenant(
        tenant_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    total = await query_repo.count_by_tenant(current_user.id)

    return QueryHistoryResponse(
        total=total,
        items=queries,
        page=offset // limit + 1,
        page_size=limit,
    )
