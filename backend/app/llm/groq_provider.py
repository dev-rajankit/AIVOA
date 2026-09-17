"""
AIVOA — Groq LLM Provider

Concrete implementation of LLMProvider using the Groq Python SDK.
Uses structured outputs (json_schema with strict: true) to guarantee
the response matches the Pydantic schema exactly.

Provides both synchronous and async methods. The async variant uses
Groq's AsyncGroq client so FastAPI endpoints never block the event loop.

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
        from groq import AsyncGroq, Groq

        self._client = Groq(api_key=api_key)
        self._async_client = AsyncGroq(api_key=api_key)

    def _build_request_params(self, system: str, user: str, schema: type[T], model: str) -> dict:
        """Build the shared request parameters for both sync and async calls."""
        schema_dict = schema.model_json_schema()
        # For structured outputs with strict=True, all properties must be required.
        if "properties" in schema_dict:
            schema_dict["required"] = list(schema_dict["properties"].keys())
            schema_dict["additionalProperties"] = False

        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema_dict,
                },
            },
            "temperature": 0.0,
        }

    def _parse_response(self, response, schema: type[T]) -> T:
        """Parse and validate an LLM response into a Pydantic model."""
        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ExtractionError("Groq returned empty content.")

        logger.info(
            "Groq structured response received (model=%s, tokens=%s)",
            getattr(response, "model", "?"),
            getattr(response.usage, "total_tokens", "?"),
        )

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"Groq returned invalid JSON: {exc}") from exc

        try:
            return schema.model_validate(parsed)
        except ValidationError as exc:
            raise ExtractionError(
                f"Groq output failed Pydantic validation: {exc}"
            ) from exc

    def structured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """Synchronous structured completion via Groq."""
        params = self._build_request_params(system, user, schema, model)
        try:
            response = self._client.chat.completions.create(**params)
        except Exception as exc:
            logger.error("Groq API call failed: %s", exc)
            raise ExtractionError(f"Groq API call failed: {exc}") from exc
        return self._parse_response(response, schema)

    async def astructured_completion(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        model: str,
    ) -> T:
        """Async structured completion via Groq — non-blocking for FastAPI."""
        params = self._build_request_params(system, user, schema, model)
        try:
            response = await self._async_client.chat.completions.create(**params)
        except Exception as exc:
            logger.error("Groq async API call failed: %s", exc)
            raise ExtractionError(f"Groq API call failed: {exc}") from exc
        return self._parse_response(response, schema)
