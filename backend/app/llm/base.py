"""
AIVOA — LLM Provider Abstraction

Provider-agnostic interface for structured LLM completions.
Per architecture §5.5: keep the graph independent from the specific LLM
provider so a future move to a different provider is a new file, not a
rewrite of every node.

Supports both sync and async structured_completion. The async variant
is used in production (FastAPI event loop); the sync variant is available
for simple scripts/tests.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol for LLM providers.

    Any provider must implement structured_completion (sync) and
    astructured_completion (async). The async variant is used by
    FastAPI to avoid blocking the event loop.
    """

    def structured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """Synchronous structured completion."""
        ...

    async def astructured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """Async structured completion — used by FastAPI."""
        ...


class ExtractionError(Exception):
    """Raised when LLM extraction fails (API error, malformed output, etc.)."""

    pass
