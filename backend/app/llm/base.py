"""
AIVOA — LLM Provider Abstraction

Provider-agnostic interface for structured LLM completions.
Per architecture §5.5: keep the graph independent from the specific LLM
provider so a future move to a different provider is a new file, not a
rewrite of every node.

Only GroqLLMProvider is implemented in this chunk.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    """
    Protocol for LLM providers.

    Any provider must implement structured_completion, which takes a
    system prompt, user message, a Pydantic model class as the response
    schema, and a model identifier, and returns a validated instance of
    that model.
    """

    def structured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """
        Request a structured completion from the LLM.

        Args:
            system: System prompt instructing the model's role.
            user: User message / data to process.
            schema: Pydantic model class defining the expected output shape.
            model: Model identifier (e.g. "openai/gpt-oss-20b").

        Returns:
            A validated instance of `schema`.

        Raises:
            ExtractionError: If the LLM response cannot be parsed/validated.
            RuntimeError: If the provider is misconfigured.
        """
        ...


class ExtractionError(Exception):
    """Raised when LLM extraction fails (API error, malformed output, etc.)."""

    pass
