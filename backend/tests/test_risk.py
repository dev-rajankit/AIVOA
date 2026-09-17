import pytest
from app.graph.state import CopilotState
from app.graph.nodes.risk_capa import risk_capa_node
from app.core.config import settings

@pytest.mark.anyio
async def test_low_risk_complaint():
    """Test 1: Low-risk complaint -> LOW classification."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Tylenol", "detailed_description": "Small scratch on the bottle label."},
        duplicate_status="UNIQUE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    assert risk is not None
    # S=5 (not safety), O=3 (UNIQUE), D=2 (obvious keyword: scratch) => RPN = 30
    assert risk["severity_score"] == 5
    assert risk["occurrence"] == 3
    assert risk["detectability"] == 2
    assert risk["rpn"] == 30
    assert risk["risk_level"] == "LOW"

@pytest.mark.anyio
async def test_safety_related_complaint():
    """Test 2: Safety-related complaint -> higher severity."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Car", "detailed_description": "Loss of control due to braking failure."},
        duplicate_status="UNIQUE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    assert risk["severity_score"] == 9  # safety keywords: braking, loss of control
    assert risk["corrective_action"].startswith("Inspect affected vehicles")

@pytest.mark.anyio
async def test_high_occurrence():
    """Test 3: High occurrence -> higher RPN via DUPLICATE status."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Widget", "detailed_description": "Normal issue."},
        duplicate_status="DUPLICATE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    assert risk["occurrence"] == 8

@pytest.mark.anyio
async def test_difficult_to_detect():
    """Test 4: Difficult-to-detect issue -> higher detection score."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Widget", "detailed_description": "An intermittent and latent defect inside."},
        duplicate_status="UNIQUE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    assert risk["detectability"] == 8 # hidden keywords: intermittent, latent, inside

@pytest.mark.anyio
async def test_rpn_calculation():
    """Test 5: RPN calculation verification."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Vehicle", "detailed_description": "Safety issue with intermittent hidden fire hazard."},
        duplicate_status="POSSIBLE_DUPLICATE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    # S=9 (safety, fire), O=5 (POSSIBLE_DUPLICATE), D=8 (hidden, intermittent)
    assert risk["severity_score"] == 9
    assert risk["occurrence"] == 5
    assert risk["detectability"] == 8
    assert risk["rpn"] == 360
    assert risk["risk_level"] == "HIGH"

@pytest.mark.anyio
async def test_capa_fields():
    """Test 6: CAPA fields are present."""
    state = CopilotState(
        session_id="test",
        merged_form={"product_name": "Pill", "detailed_description": "Pill is discolored."},
        duplicate_status="UNIQUE"
    )
    result = risk_capa_node(state)
    risk = result["risk_assessment"]
    assert "corrective_action" in risk
    assert "preventive_action" in risk
    assert risk["corrective_action"] is not None
    assert risk["preventive_action"] is not None

@pytest.mark.anyio
async def test_capa_generation_failure_fallback():
    """Test 7: Empty complaint returns None safely."""
    state = CopilotState(
        session_id="test",
        merged_form={},
        duplicate_status="UNIQUE"
    )
    result = risk_capa_node(state)
    assert result["risk_assessment"] is None
