"""
AIVOA — Extraction Node

LangGraph node responsible for extracting structured complaint fields
from user input via an LLM provider.

The node orchestrates:
1. Validate input size
2. Call LLM provider with the extraction prompt
3. Validate result against ComplaintFields
4. Return extracted fields to state

The provider is injected via make_extraction_node() so tests can
substitute a FakeLLMProvider without calling Groq.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from app.graph.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    MAX_EXTRACTION_INPUT_LENGTH,
)
from app.graph.state import CopilotState
from app.llm.base import ExtractionError, LLMProvider
from app.schemas.complaint import ComplaintFields

logger = logging.getLogger(__name__)


def make_extraction_node(
    provider: LLMProvider,
    model: str,
) -> Callable[[CopilotState], dict[str, Any]]:
    """
    Factory that creates an extraction node bound to a specific provider
    and model. This is how dependency injection works:

    Production:
        make_extraction_node(GroqLLMProvider(key), settings.EXTRACTION_MODEL)

    Tests:
        make_extraction_node(FakeLLMProvider(), "fake-model")
    """

    def extraction_node(state: CopilotState) -> dict[str, Any]:
        """Extract structured complaint fields from user input via LLM."""
        user_input = state.get("user_input", "")

        # --- Guard: empty input ---
        if not user_input or not user_input.strip():
            logger.warning("Extraction received empty user input.")
            return {"extracted_fields": {}}

        # --- Guard: input too long ---
        if len(user_input) > MAX_EXTRACTION_INPUT_LENGTH:
            raise ExtractionError(
                f"User input exceeds maximum length "
                f"({len(user_input)} > {MAX_EXTRACTION_INPUT_LENGTH} chars). "
                f"Please shorten the complaint text."
            )

        # --- Call the provider ---
        try:
            result: ComplaintFields = provider.structured_completion(
                system=EXTRACTION_SYSTEM_PROMPT,
                user=user_input,
                schema=ComplaintFields,
                model=model,
            )
        except ExtractionError:
            # Re-raise — do NOT fabricate successful extraction on failure.
            raise
        except Exception as exc:
            raise ExtractionError(
                f"Unexpected error during extraction: {exc}"
            ) from exc

        # Convert to dict, excluding None values so the merge node
        # correctly ignores fields the LLM didn't find.
        extracted = result.model_dump(exclude_none=True)

        logger.info(
            "Extraction produced %d fields: %s",
            len(extracted),
            list(extracted.keys()),
        )

        return {"extracted_fields": extracted}

    return extraction_node
