"""
Tests for Pydantic schema validation.

All tests are pure Python — no database or LLM calls required.
Each test verifies one specific validation behavior of the canonical
data contracts.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import (
    ComplaintFields,
    RiskAssessment,
    ExtractionResult,
    CopilotMessageRequest,
    CopilotMessageResponse,
)


# =========================================================================
# 1. ComplaintFields — optionality
# =========================================================================


def test_empty_complaint_fields_is_valid():
    """All fields are Optional, so an empty object must be valid."""
    fields = ComplaintFields()
    assert fields.complaint_source is None
    assert fields.customer_name is None
    assert fields.product_name is None
    assert fields.dosage_form is None


def test_partial_complaint_fields_is_valid():
    """Only some fields provided — common during AI extraction."""
    fields = ComplaintFields(
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules 500mg",
        batch_lot_number="AMX24601",
    )
    assert fields.customer_name == "Apollo Pharmacy"
    assert fields.product_name == "Amoxicillin Capsules 500mg"
    assert fields.batch_lot_number == "AMX24601"
    assert fields.complaint_source is None  # not provided
    assert fields.dosage_form is None       # not provided


def test_full_complaint_fields_is_valid():
    """All fields provided — after complete extraction."""
    fields = ComplaintFields(
        complaint_source="Email",
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules 500mg",
        product_strength_grade="500mg",
        batch_lot_number="AMX24601",
        affected_quantity="50 kg (2 HDPE Drums)",
        manufacturing_date=date(2026, 3, 12),
        expiry_date=date(2028, 2, 28),
        dosage_form="FDF",
        complaint_type="Discoloration",
        complaint_date=date(2026, 9, 14),
        detailed_description="Discolored capsules reported in batch AMX24601.",
    )
    assert fields.complaint_source == "Email"
    assert fields.manufacturing_date == date(2026, 3, 12)
    assert fields.dosage_form == "FDF"
    assert fields.detailed_description is not None


# =========================================================================
# 2. ComplaintFields — dosage_form validation
# =========================================================================


def test_dosage_form_api_accepted():
    """API (Active Pharmaceutical Ingredient) is a valid dosage form."""
    fields = ComplaintFields(dosage_form="API")
    assert fields.dosage_form == "API"


def test_dosage_form_fdf_accepted():
    """FDF (Finished Dosage Form) is a valid dosage form."""
    fields = ComplaintFields(dosage_form="FDF")
    assert fields.dosage_form == "FDF"


def test_dosage_form_invalid_rejected():
    """Dosage form must be exactly 'API' or 'FDF'."""
    with pytest.raises(ValidationError) as exc_info:
        ComplaintFields(dosage_form="TABLET")
    assert "dosage_form" in str(exc_info.value)


# =========================================================================
# 3. ComplaintFields — date validation
# =========================================================================


def test_valid_date_accepted():
    """Structured date objects should be accepted."""
    fields = ComplaintFields(
        manufacturing_date=date(2026, 3, 12),
        complaint_date=date(2026, 9, 14),
    )
    assert fields.manufacturing_date == date(2026, 3, 12)
    assert fields.complaint_date == date(2026, 9, 14)


def test_iso_date_string_coerced():
    """Pydantic v2 coerces ISO date strings to date objects."""
    fields = ComplaintFields(manufacturing_date="2026-03-12")
    assert fields.manufacturing_date == date(2026, 3, 12)


def test_invalid_date_rejected():
    """Non-date values must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ComplaintFields(manufacturing_date="not-a-date")
    assert "manufacturing_date" in str(exc_info.value)


# =========================================================================
# 4. ComplaintFields — extra fields rejected
# =========================================================================


def test_extra_fields_rejected():
    """Extra fields must be rejected to prevent schema drift."""
    with pytest.raises(ValidationError):
        ComplaintFields(nonexistent_field="value")


# =========================================================================
# 5. RiskAssessment — severity validation
# =========================================================================


def test_severity_minor_accepted():
    """Minor severity is valid."""
    risk = RiskAssessment(severity="Minor")
    assert risk.severity == "Minor"


def test_severity_major_accepted():
    """Major severity is valid."""
    risk = RiskAssessment(severity="Major")
    assert risk.severity == "Major"


def test_severity_critical_accepted():
    """Critical severity is valid."""
    risk = RiskAssessment(severity="Critical")
    assert risk.severity == "Critical"


def test_severity_invalid_rejected():
    """Severity must be exactly Minor, Major, or Critical."""
    with pytest.raises(ValidationError) as exc_info:
        RiskAssessment(severity="Low")
    assert "severity" in str(exc_info.value)


# =========================================================================
# 6. RiskAssessment — optional fields and FMEA scores
# =========================================================================


def test_risk_minimal_valid():
    """Only severity is required."""
    risk = RiskAssessment(severity="Minor")
    assert risk.occurrence is None
    assert risk.detectability is None
    assert risk.rpn is None
    assert risk.regulatory_flag is False


def test_risk_full_valid():
    """All fields provided."""
    risk = RiskAssessment(
        severity="Critical",
        occurrence=8,
        detectability=3,
        rpn=240,
        recommended_action="Route to QA investigation and issue replacement",
        root_cause_hint="Possible moisture ingress during storage",
        capa_recommendation="Review packaging process for seal integrity",
        regulatory_flag=True,
        ai_reasoning_summary="Critical severity due to visible contamination",
        model_used="openai/gpt-oss-120b",
    )
    assert risk.severity == "Critical"
    assert risk.occurrence == 8
    assert risk.rpn == 240
    assert risk.regulatory_flag is True


def test_occurrence_out_of_range_rejected():
    """FMEA occurrence must be 1-10."""
    with pytest.raises(ValidationError):
        RiskAssessment(severity="Minor", occurrence=11)


def test_detectability_out_of_range_rejected():
    """FMEA detectability must be 1-10."""
    with pytest.raises(ValidationError):
        RiskAssessment(severity="Minor", detectability=0)


# =========================================================================
# 7. ExtractionResult — wraps ComplaintFields
# =========================================================================


def test_extraction_result_valid():
    """ExtractionResult wraps ComplaintFields for structured LLM output."""
    result = ExtractionResult(
        fields=ComplaintFields(
            customer_name="Apollo Pharmacy",
            product_name="Amoxicillin Capsules 500mg",
        )
    )
    assert result.fields.customer_name == "Apollo Pharmacy"


def test_extraction_result_empty_fields_valid():
    """Extraction may find no fields — still valid."""
    result = ExtractionResult(fields=ComplaintFields())
    assert result.fields.product_name is None


# =========================================================================
# 8. ComplaintFields as form_patch — partial update
# =========================================================================


def test_partial_form_patch():
    """A patch with only batch_lot_number represents 'change only this field'."""
    patch = ComplaintFields(batch_lot_number="AMX24602")
    assert patch.batch_lot_number == "AMX24602"
    assert patch.customer_name is None
    assert patch.product_name is None
    assert patch.complaint_date is None


# =========================================================================
# 9. CopilotMessageRequest validation
# =========================================================================


def test_copilot_request_valid():
    """Basic copilot request with required fields."""
    req = CopilotMessageRequest(
        session_id="sess-001",
        message="Log a new complaint about discolored capsules.",
    )
    assert req.session_id == "sess-001"
    assert req.input_type == "text"  # default
    assert req.complaint_id is None  # optional


def test_copilot_request_with_complaint_id():
    """Request referencing an existing complaint."""
    req = CopilotMessageRequest(
        session_id="sess-001",
        complaint_id="11111111-1111-1111-1111-111111111111",
        message="Change the batch number to AMX24602.",
    )
    assert req.complaint_id == "11111111-1111-1111-1111-111111111111"


def test_copilot_request_empty_message_rejected():
    """Message must not be empty."""
    with pytest.raises(ValidationError):
        CopilotMessageRequest(session_id="sess-001", message="")


def test_copilot_request_document_type():
    """Input type 'document' for file uploads."""
    req = CopilotMessageRequest(
        session_id="sess-001",
        message="Process this PDF complaint.",
        input_type="document",
    )
    assert req.input_type == "document"


# =========================================================================
# 10. CopilotMessageResponse — form_patch and risk_patch
# =========================================================================


def test_copilot_response_with_form_patch():
    """Response carries a partial complaint update."""
    resp = CopilotMessageResponse(
        assistant_reply="I've updated the batch number.",
        form_patch=ComplaintFields(batch_lot_number="AMX24602"),
        changed_fields=["batch_lot_number"],
    )
    assert resp.form_patch is not None
    assert resp.form_patch.batch_lot_number == "AMX24602"
    assert resp.risk_patch is None


def test_copilot_response_with_risk_patch():
    """Response carries a risk assessment update."""
    resp = CopilotMessageResponse(
        assistant_reply="Risk assessment complete.",
        risk_patch=RiskAssessment(
            severity="Major",
            recommended_action="Route to QA investigation",
        ),
        changed_fields=[],
    )
    assert resp.risk_patch is not None
    assert resp.risk_patch.severity == "Major"


def test_copilot_response_minimal():
    """Minimal response — just a reply, no patches."""
    resp = CopilotMessageResponse(
        assistant_reply="I don't understand, could you rephrase?",
    )
    assert resp.form_patch is None
    assert resp.risk_patch is None
    assert resp.changed_fields == []


def test_changed_fields_is_string_list():
    """changed_fields must be a list of strings."""
    resp = CopilotMessageResponse(
        assistant_reply="Updated.",
        changed_fields=["batch_lot_number", "affected_quantity"],
    )
    assert isinstance(resp.changed_fields, list)
    assert all(isinstance(f, str) for f in resp.changed_fields)
    assert len(resp.changed_fields) == 2


# =========================================================================
# 11. JSON schema generation — for Groq strict mode
# =========================================================================


def test_complaint_fields_json_schema_generated():
    """ComplaintFields must produce a valid JSON schema for Groq strict mode."""
    schema = ComplaintFields.model_json_schema()
    assert "properties" in schema
    assert "complaint_source" in schema["properties"]
    assert "dosage_form" in schema["properties"]
    assert "batch_lot_number" in schema["properties"]


def test_risk_assessment_json_schema_generated():
    """RiskAssessment must produce a valid JSON schema."""
    schema = RiskAssessment.model_json_schema()
    assert "properties" in schema
    assert "severity" in schema["properties"]
    assert "rpn" in schema["properties"]
