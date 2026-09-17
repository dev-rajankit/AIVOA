import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app

@pytest.fixture
def sample_report_payload():
    return {
        "complaint_id": "TEST1234",
        "complaint": {
            "customer_name": "Test Customer",
            "product_name": "Test Product",
            "complaint_source": "Email",
            "detailed_description": "A very long detailed description that should wrap properly in the PDF generation test without causing any FPDF layout crashing issues."
        },
        "risk": {
            "severity": "Major",
            "occurrence": 5,
            "detectability": 3,
            "rpn": 15,
            "recommended_action": "Test action",
            "regulatory_flag": False
        }
    }

@pytest.mark.anyio
async def test_pdf_generation_complete_result(sample_report_payload):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/pdf", json=sample_report_payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "AIVOA_TEST1234_report.pdf" in response.headers["content-disposition"]
    assert len(response.content) > 1000  # valid PDF should have size

@pytest.mark.anyio
async def test_pdf_generation_incomplete_result():
    # Only complaint_id and empty complaint
    payload = {
        "complaint_id": "TEST999",
        "complaint": {},
        "risk": None
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/pdf", json=payload)
        
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000

@pytest.mark.anyio
async def test_pdf_generation_missing_fields():
    # Omitting complaint field completely
    payload = {
        "complaint_id": "TEST999"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/pdf", json=payload)
        
    assert response.status_code == 422  # validation error

@patch("app.api.report.send_report_email")
@pytest.mark.anyio
async def test_email_valid_request(mock_send, sample_report_payload):
    payload = {**sample_report_payload, "recipient_email": "test@example.com"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/email", json=payload)
        
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Email successfully sent to test@example.com"}
    mock_send.assert_called_once()

@pytest.mark.anyio
async def test_email_invalid_email_format(sample_report_payload):
    payload = {**sample_report_payload, "recipient_email": "not-an-email"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/email", json=payload)
        
    assert response.status_code == 422  # Pydantic validation error

@patch("app.api.report.send_report_email")
@pytest.mark.anyio
async def test_email_provider_failure(mock_send, sample_report_payload):
    mock_send.side_effect = RuntimeError("SMTP connection failed")
    payload = {**sample_report_payload, "recipient_email": "test@example.com"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/report/email", json=payload)
        
    assert response.status_code == 502
    assert "SMTP connection failed" in response.json()["detail"]
