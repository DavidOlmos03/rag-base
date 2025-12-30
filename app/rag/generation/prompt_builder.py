"""
Prompt template builder for RAG queries.
"""

from app.core.logging import get_logger
from app.domain.interfaces.retriever import RetrievedChunk

logger = get_logger(__name__)


class PromptBuilder:
    """Build prompts for RAG queries."""

    DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant. Answer the user's question based on the provided context.
If the context doesn't contain relevant information, say so clearly.
Be concise and accurate in your responses."""

    DEFAULT_USER_TEMPLATE = """Context information is below:
---
{context}
---

Using the context information above, answer the following question:
{query}

Answer:"""

    def __init__(
        self,
        system_prompt: str | None = None,
        user_template: str | None = None,
    ):
        """Initialize prompt builder.

        Args:
            system_prompt: Custom system prompt
            user_template: Custom user message template
        """
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.user_template = user_template or self.DEFAULT_USER_TEMPLATE

    def build_prompt(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[str, str]:
        """Build system and user prompts.

        Args:
            query: User query
            chunks: Retrieved context chunks

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Format context from chunks
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(f"[{idx}] {chunk.content}")

        context = "\n\n".join(context_parts)

        # Build user prompt
        user_prompt = self.user_template.format(
            context=context,
            query=query,
        )

        logger.debug(
            "prompt_built",
            query_length=len(query),
            num_chunks=len(chunks),
            context_length=len(context),
        )

        return self.system_prompt, user_prompt

    def build_messages(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        """Build chat messages for LLM.

        Args:
            query: User query
            chunks: Retrieved context chunks

        Returns:
            List of message dicts
        """
        system_prompt, user_prompt = self.build_prompt(query, chunks)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return messages
