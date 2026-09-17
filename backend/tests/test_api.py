import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.graph.graph import build_graph
from app.api.copilot import get_graph
from app.schemas.complaint import ComplaintFields

# Fake provider to bypass real LLM
class FakeLLMProvider:
    async def astructured_completion(self, *, system, user, schema, model):
        if "error" in user.lower():
            from app.llm.base import ExtractionError
            raise ExtractionError("Fake error")
            
        return schema(
            product_name="Amoxicillin Capsules 500mg",
            batch_lot_number="AMX24602" if "amx24602" in user.lower() else "AMX24601",
            affected_quantity="48 capsules" if "48 capsules" in user.lower() else None,
            dosage_form="FDF",
        )

# Override the dependency for testing
@pytest.fixture
def fake_graph():
    return build_graph(llm_provider=FakeLLMProvider(), extraction_model="fake-model")

@pytest.fixture
def client(fake_graph):
    # Override the graph dependency
    app.dependency_overrides[get_graph] = lambda: fake_graph
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_new_complaint_api(client):
    payload = {
        "session_id": "test-session-1",
        "message": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500mg, batch AMX24601"
    }
    
    response = await client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["intent"] == "new_complaint"
    assert "form_patch" in data
    assert data["form_patch"]["batch_lot_number"] == "AMX24601"
    assert "assistant_reply" in data
    assert data["completeness_pct"] > 0
    assert "changed_fields" in data
    assert "batch_lot_number" in data["changed_fields"]

@pytest.mark.anyio
async def test_correction_api(client):
    # Provide an existing current_form
    payload = {
        "session_id": "test-session-2",
        "message": "Sorry, the batch number is AMX24602 and affected quantity is 48 capsules.",
        "current_form": {
            "product_name": "Amoxicillin Capsules 500mg",
            "batch_lot_number": "AMX24601"
        }
    }
    
    response = await client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["intent"] == "edit_complaint"
    
    patch = data.get("form_patch")
    assert patch is not None
    assert patch["batch_lot_number"] == "AMX24602"
    assert patch["affected_quantity"] == "48 capsules"
    
    # product_name did not change, so it shouldn't be in the patch if we only return changed fields,
    # but currently we return the full extraction patch from the provider which is then merged.
    # Actually, the logic in copilot.py says:
    # patch_dict = {k: merged[k] for k in changed_keys if k in merged}
    # So product_name should NOT be in the changed fields and thus not in the patch.
    changed = data.get("changed_fields")
    assert "batch_lot_number" in changed
    assert "affected_quantity" in changed
    assert "product_name" not in changed
    assert patch.get("product_name") is None

@pytest.mark.anyio
async def test_api_validation(client):
    # Missing session_id
    payload = {
        "message": "hello"
    }
    response = await client.post("/api/copilot/message", json=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_provider_failure(client):
    payload = {
        "session_id": "test-session-4",
        "message": "trigger an error here"
    }
    response = await client.post("/api/copilot/message", json=payload)
    assert response.status_code == 500
