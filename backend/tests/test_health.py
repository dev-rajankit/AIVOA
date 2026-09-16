"""
Tests for the /health endpoint.

Verifies that the FastAPI application starts correctly and responds
to health checks with the expected shape.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_returns_200():
    """GET /health should return HTTP 200 with status 'ok'."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.anyio
async def test_health_response_shape():
    """GET /health response should contain exactly the expected keys."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    data = response.json()
    assert set(data.keys()) == {"status"}
