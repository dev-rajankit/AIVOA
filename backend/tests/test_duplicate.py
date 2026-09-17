import pytest
from httpx import AsyncClient

import uuid
from unittest.mock import patch, AsyncMock

from app.db.models import DuplicateStatus, Complaint
from app.graph.state import CopilotState
from app.graph.nodes.duplicate import duplicate_node, get_embedding_model

# Pre-compute vectors synchronously to avoid event loop blocking
_model = get_embedding_model()
vec_exact = _model.encode("apollo pharmacy reported discolored capsules in amoxicillin capsules 500mg, batch amx24601 product: amoxicillin capsules 500mg type: discoloration batch: amx24601").tolist()
vec_similar = _model.encode("capsules are looking weird color and off-white instead of normal. product: amoxicillin capsules type: appearance issue").tolist()

@pytest.fixture(autouse=True)
def mock_db():
    with patch("app.graph.nodes.duplicate.async_session_factory") as mock_factory:
        mock_db_instance = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_db_instance
        
        class MockResult:
            def scalars(self):
                return self
            def all(self):
                c1 = Complaint(
                    id=uuid.uuid4(),
                    detailed_description="Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500mg, batch AMX24601"
                )
                c1.embedding = vec_exact
                
                c2 = Complaint(
                    id=uuid.uuid4(),
                    detailed_description="Capsules are looking weird color and off-white instead of normal."
                )
                c2.embedding = vec_similar
                
                return [c1, c2]
        
        mock_db_instance.execute.return_value = MockResult()
        
        yield mock_db_instance



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
