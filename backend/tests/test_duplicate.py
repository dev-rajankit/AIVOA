import pytest
from httpx import AsyncClient

from app.db.models import DuplicateStatus, Complaint
from app.graph.state import CopilotState
from app.graph.nodes.duplicate import duplicate_node

@pytest.mark.anyio
async def test_duplicate_exact_match():
    # This should match CC-2026-00001
    state = CopilotState(
        session_id="test-session",
        complaint_id=None,
        user_input="Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500mg, batch AMX24601",
        input_type="text",
        intent="new_complaint",
        current_form={},
        extracted_fields={},
        merged_form={
            "detailed_description": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500mg, batch AMX24601",
            "product_name": "Amoxicillin Capsules 500mg",
            "batch_lot_number": "AMX24601",
            "complaint_type": "Discoloration"
        },
        changed_fields=[],
        completeness_pct=0.0,
        missing_fields=[],
        duplicate_status="UNIQUE",
        duplicate_matches=[],
        risk_assessment={},
        assistant_reply=""
    )
    
    result = await duplicate_node(state)
    
    assert result["duplicate_status"] == DuplicateStatus.DUPLICATE.value
    assert len(result["duplicate_matches"]) > 0
    
@pytest.mark.anyio
async def test_duplicate_similar_wording():
    # Testing different wording for the same conceptual issue
    state = CopilotState(
        session_id="test-session",
        complaint_id=None,
        user_input="Amox capsules looking weird color",
        input_type="text",
        intent="new_complaint",
        current_form={},
        extracted_fields={},
        merged_form={
            "detailed_description": "Capsules are looking weird color and off-white instead of normal.",
            "product_name": "Amoxicillin Capsules",
            "complaint_type": "Appearance issue"
        },
        changed_fields=[],
        completeness_pct=0.0,
        missing_fields=[],
        duplicate_status="UNIQUE",
        duplicate_matches=[],
        risk_assessment={},
        assistant_reply=""
    )
    
    result = await duplicate_node(state)
    
    # Depending on threshold, could be POSSIBLE_DUPLICATE or DUPLICATE. 
    # Just asserting it caught a match.
    assert result["duplicate_status"] in [DuplicateStatus.DUPLICATE.value, DuplicateStatus.POSSIBLE_DUPLICATE.value]
    assert len(result["duplicate_matches"]) > 0

@pytest.mark.anyio
async def test_duplicate_unrelated():
    # Completely unrelated
    state = CopilotState(
        session_id="test-session",
        complaint_id=None,
        user_input="The car's brake pedal is making a squeaking noise.",
        input_type="text",
        intent="new_complaint",
        current_form={},
        extracted_fields={},
        merged_form={
            "detailed_description": "The car's brake pedal is making a squeaking noise.",
            "product_name": "Brake Pedal",
            "complaint_type": "Noise"
        },
        changed_fields=[],
        completeness_pct=0.0,
        missing_fields=[],
        duplicate_status="UNIQUE",
        duplicate_matches=[],
        risk_assessment={},
        assistant_reply=""
    )
    
    result = await duplicate_node(state)
    
    assert result["duplicate_status"] == DuplicateStatus.UNIQUE.value
