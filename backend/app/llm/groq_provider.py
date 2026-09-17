"""
AIVOA — Groq LLM Provider

Concrete implementation of LLMProvider using the Groq Python SDK.
Uses structured outputs (json_schema with strict: true) to guarantee
the response matches the Pydantic schema exactly.

Per architecture §5.5: Groq is the mandatory primary provider.
"""

from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import ExtractionError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GroqLLMProvider:
    """
    LLM provider backed by the Groq API.

    Initialized once with an API key; reused across requests.
    Uses json_schema response_format with strict: true for constrained
    decoding — the model is forced to produce valid JSON matching the
    schema, removing an entire category of malformed-output bugs.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is required but not set. "
                "Set it in your .env file or environment variables."
            )
        # Lazy import so tests that don't use the real provider
        # don't need the groq package installed at import time.
        from groq import Groq

        self._client = Groq(api_key=api_key)

    def structured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """
        Request a structured completion from Groq.

        Uses json_schema response_format with strict: true so the model's
        output is constrained to match the Pydantic schema exactly.

        Returns a validated Pydantic model instance.

        Raises:
            ExtractionError: On API failure, malformed output, or validation error.
        """
        json_schema = schema.model_json_schema()

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "strict": True,
                        "schema": json_schema,
                    },
                },
                temperature=0.0,
            )
        except Exception as exc:
            logger.error("Groq API call failed: %s", exc)
            raise ExtractionError(f"Groq API call failed: {exc}") from exc

        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ExtractionError("Groq returned empty content.")

        logger.info(
            "Groq structured response received (model=%s, tokens=%s)",
            model,
            getattr(response.usage, "total_tokens", "?"),
        )

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"Groq returned invalid JSON: {exc}"
            ) from exc

        try:
            return schema.model_validate(parsed)
        except ValidationError as exc:
            raise ExtractionError(
                f"Groq output failed Pydantic validation: {exc}"
            ) from exc
