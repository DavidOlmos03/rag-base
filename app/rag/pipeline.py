"""
RAG Pipeline orchestrator - coordinates the full RAG flow.
"""

import time
import uuid
from typing import AsyncGenerator

from app.core.logging import get_logger
from app.domain.interfaces.llm_client import LLMClient, LLMMessage
from app.domain.interfaces.retriever import Retriever
from app.rag.generation.context_compressor import ContextCompressor
from app.rag.generation.prompt_builder import PromptBuilder

logger = get_logger(__name__)


class RAGPipeline:
    """Orchestrates the complete RAG pipeline."""

    def __init__(
        self,
        retriever: Retriever,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
        context_compressor: ContextCompressor | None = None,
    ):
        """Initialize RAG pipeline.

        Args:
            retriever: Retriever implementation
            llm_client: LLM client implementation
            prompt_builder: Optional prompt builder
            context_compressor: Optional context compressor
        """
        self.retriever = retriever
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.context_compressor = context_compressor or ContextCompressor()

    async def query(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        use_hybrid: bool = False,
    ) -> dict:
        """Execute RAG query.

        Args:
            query: User query
            tenant_id: Tenant identifier
            top_k: Number of chunks to retrieve
            score_threshold: Minimum similarity score
            temperature: LLM temperature
            max_tokens: Max tokens to generate
            use_hybrid: Use hybrid retrieval

        Returns:
            Query result with answer and metadata
        """
        start_time = time.time()
        query_id = uuid.uuid4()

        logger.info(
            "rag_query_started",
            query_id=str(query_id),
            tenant_id=tenant_id,
            query_length=len(query),
        )

        try:
            # Step 1: Retrieval
            if use_hybrid:
                chunks = await self.retriever.hybrid_retrieve(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=top_k,
                )
            else:
                chunks = await self.retriever.retrieve(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )

            logger.info("retrieval_complete", query_id=str(query_id), chunks_found=len(chunks))

            # Step 2: Context compression
            compressed_chunks = await self.context_compressor.compress(
                chunks=chunks,
                strategy="token_limit",
            )

            logger.info(
                "context_compressed",
                query_id=str(query_id),
                original_chunks=len(chunks),
                compressed_chunks=len(compressed_chunks),
            )

            # Step 3: Build prompt
            messages_dict = self.prompt_builder.build_messages(query, compressed_chunks)
            messages = [LLMMessage(**msg) for msg in messages_dict]

            # Step 4: Generate answer
            response = await self.llm_client.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            processing_time = time.time() - start_time

            logger.info(
                "rag_query_complete",
                query_id=str(query_id),
                processing_time=processing_time,
                tokens_used=response.usage.total_tokens,
            )

            # Build response
            result = {
                "query_id": query_id,
                "query": query,
                "answer": response.content,
                "contexts": [
                    {
                        "content": chunk.content,
                        "score": chunk.score,
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.chunk_id,
                        "metadata": chunk.metadata,
                    }
                    for chunk in compressed_chunks
                ],
                "model_used": response.model,
                "tokens_used": response.usage.total_tokens,
                "processing_time": processing_time,
            }

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "rag_query_failed",
                query_id=str(query_id),
                error=str(e),
                processing_time=processing_time,
            )
            raise

    async def query_stream(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        use_hybrid: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Execute RAG query with streaming response.

        Args:
            query: User query
            tenant_id: Tenant identifier
            top_k: Number of chunks to retrieve
            score_threshold: Minimum similarity score
            temperature: LLM temperature
            max_tokens: Max tokens to generate
            use_hybrid: Use hybrid retrieval

        Yields:
            Response chunks as they arrive
        """
        query_id = uuid.uuid4()

        logger.info(
            "rag_query_stream_started",
            query_id=str(query_id),
            tenant_id=tenant_id,
        )

        try:
            # Retrieval and compression (same as non-streaming)
            if use_hybrid:
                chunks = await self.retriever.hybrid_retrieve(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=top_k,
                )
            else:
                chunks = await self.retriever.retrieve(
                    query=query,
                    tenant_id=tenant_id,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )

            compressed_chunks = await self.context_compressor.compress(
                chunks=chunks,
                strategy="token_limit",
            )

            # Build prompt
            messages_dict = self.prompt_builder.build_messages(query, compressed_chunks)
            messages = [LLMMessage(**msg) for msg in messages_dict]

            # Stream generation
            async for chunk in self.llm_client.generate_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk

            logger.info("rag_query_stream_complete", query_id=str(query_id))

        except Exception as e:
            logger.error("rag_query_stream_failed", query_id=str(query_id), error=str(e))
            raise
