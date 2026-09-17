"""
Tests for the LangGraph workflow.

These tests use a FakeLLMProvider so they never call Groq.
No API key, network, or database required.
"""

from app.graph.graph import build_graph, copilot_graph
from app.graph.state import CopilotState
from app.schemas.complaint import ComplaintFields


# ─── FakeLLMProvider ────────────────────────────────────────────────────────

class FakeLLMProvider:
    """
    Deterministic LLM provider for testing.

    Returns a pre-configured ComplaintFields based on simple keyword
    detection in the user message. This mirrors the old Chunk 4 mock
    behavior but goes through the real provider interface.
    """

    def structured_completion(self, *, system, user, schema, model):
        text = user.lower()
        fields = {}

        if "paracetamol" in text:
            fields["product_name"] = "Paracetamol"
        if "amoxicillin" in text:
            fields["product_name"] = "Amoxicillin Capsules 500mg"

        if "b123" in text:
            fields["batch_lot_number"] = "B123"
        elif "amx24601" in text:
            fields["batch_lot_number"] = "AMX24601"
        elif "amx24602" in text:
            fields["batch_lot_number"] = "AMX24602"

        if "fdf" in text or "capsules" in text or "tablets" in text:
            fields["dosage_form"] = "FDF"
        elif "api" in text:
            fields["dosage_form"] = "API"

        if "48 capsules" in text:
            fields["affected_quantity"] = "48 capsules"

        return ComplaintFields(**fields)


def _build_test_graph():
    """Build a graph with the FakeLLMProvider for testing."""
    return build_graph(
        llm_provider=FakeLLMProvider(),
        extraction_model="fake-test-model",
    )


# ─── Existing Chunk 4 tests (updated to use FakeLLMProvider) ────────────────


def test_graph_structure():
    """Verify graph compiles and expected nodes exist."""
    assert copilot_graph is not None
    nodes = copilot_graph.nodes
    expected_nodes = {
        "router", "extraction", "merge", "completeness",
        "duplicate", "risk_capa", "compose_response"
    }
    for node in expected_nodes:
        assert node in nodes


def test_basic_graph_execution():
    """Provide a simple user input and ensure state flows."""
    graph = _build_test_graph()
    initial_state = {
        "session_id": "test-session",
        "user_input": "Just a test input",
        "current_form": {}
    }

    result = graph.invoke(initial_state)

    assert "assistant_reply" in result
    assert "completeness_pct" in result
    assert "missing_fields" in result
    assert "duplicate_matches" in result
    assert result["intent"] == "new_complaint"


def test_extraction_mock():
    """Ensure extraction logic correctly pulls from input."""
    graph = _build_test_graph()
    initial_state = {
        "session_id": "1",
        "user_input": "Product Paracetamol batch B123 and 48 capsules fdf",
        "current_form": {}
    }

    result = graph.invoke(initial_state)

    extracted = result.get("extracted_fields", {})
    assert extracted.get("product_name") == "Paracetamol"
    assert extracted.get("batch_lot_number") == "B123"
    assert extracted.get("dosage_form") == "FDF"
    assert extracted.get("affected_quantity") == "48 capsules"


def test_merge_logic():
    """Verify merge updates only non-nulls and populates changed_fields."""
    graph = _build_test_graph()
    initial_state = {
        "session_id": "1",
        "user_input": "Correction: batch AMX24602",
        "current_form": {
            "product_name": "Paracetamol",
            "batch_lot_number": "B123"
        }
    }

    result = graph.invoke(initial_state)

    merged = result["merged_form"]
    changed = result["changed_fields"]

    assert merged["product_name"] == "Paracetamol"  # Preserved
    assert merged["batch_lot_number"] == "AMX24602"  # Overwritten
    assert "batch_lot_number" in changed
    assert "product_name" not in changed


def test_completeness_calculation():
    """Verify required fields and API vs FDF logic."""
    graph = _build_test_graph()

    # API case
    state_api = {
        "session_id": "1",
        "user_input": "API paracetamol",
        "current_form": {}
    }
    res_api = graph.invoke(state_api)
    assert res_api["completeness_pct"] == (2 / 3 * 100)
    assert "batch_lot_number" in res_api["missing_fields"]
    assert "affected_quantity" not in res_api["missing_fields"]

    # FDF case
    state_fdf = {
        "session_id": "1",
        "user_input": "FDF amoxicillin",
        "current_form": {}
    }
    res_fdf = graph.invoke(state_fdf)
    assert res_fdf["completeness_pct"] == 50.0
    assert "batch_lot_number" in res_fdf["missing_fields"]
    assert "affected_quantity" in res_fdf["missing_fields"]


def test_full_graph_state():
    """Verify all expected major fields are present in the final state."""
    graph = _build_test_graph()
    initial_state = {
        "session_id": "session_full",
        "user_input": "Product Paracetamol batch B123 dosage form API",
        "current_form": {}
    }

    result = graph.invoke(initial_state)

    expected_keys = {
        "session_id", "user_input", "input_type", "intent",
        "current_form", "extracted_fields", "merged_form",
        "changed_fields", "completeness_pct", "missing_fields",
        "duplicate_matches", "risk_assessment", "assistant_reply"
    }

    for key in expected_keys:
        assert key in result

    # Verify risk_capa mocked properly because product_name is Paracetamol
    assert "severity" in result["risk_assessment"]
    assert result["risk_assessment"]["severity"] == "Major"
