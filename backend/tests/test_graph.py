from app.graph.graph import copilot_graph
from app.graph.state import CopilotState

def test_graph_structure():
    """Test 6: Verify graph compiles and expected nodes exist."""
    assert copilot_graph is not None
    # LangGraph CompiledStateGraph has a nodes property
    nodes = copilot_graph.nodes
    expected_nodes = {
        "router", "extraction", "merge", "completeness", 
        "duplicate", "risk_capa", "compose_response"
    }
    for node in expected_nodes:
        assert node in nodes

def test_basic_graph_execution():
    """Test 1: Provide a simple user input and ensure state flows."""
    initial_state = {
        "session_id": "test-session",
        "user_input": "Just a test input",
        "current_form": {}
    }
    
    result = copilot_graph.invoke(initial_state)
    
    assert "assistant_reply" in result
    assert "completeness_pct" in result
    assert "missing_fields" in result
    assert "duplicate_matches" in result
    assert result["intent"] == "new_complaint"

def test_extraction_mock():
    """Test 2: Ensure extraction logic correctly pulls from input."""
    initial_state = {
        "session_id": "1",
        "user_input": "Product Paracetamol batch B123 and 48 capsules fdf",
        "current_form": {}
    }
    
    result = copilot_graph.invoke(initial_state)
    
    extracted = result.get("extracted_fields", {})
    assert extracted.get("product_name") == "Paracetamol"
    assert extracted.get("batch_lot_number") == "B123"
    assert extracted.get("dosage_form") == "FDF"
    assert extracted.get("affected_quantity") == "48 capsules"

def test_merge_logic():
    """Test 3: Verify merge updates only non-nulls and populates changed_fields."""
    initial_state = {
        "session_id": "1",
        "user_input": "Correction: batch AMX24602",
        "current_form": {
            "product_name": "Paracetamol",
            "batch_lot_number": "B123"
        }
    }
    
    result = copilot_graph.invoke(initial_state)
    
    merged = result["merged_form"]
    changed = result["changed_fields"]
    
    assert merged["product_name"] == "Paracetamol" # Preserved
    assert merged["batch_lot_number"] == "AMX24602" # Overwritten
    assert "batch_lot_number" in changed
    assert "product_name" not in changed

def test_completeness_calculation():
    """Test 4: Verify required fields and API vs FDF logic."""
    # API case
    state_api = {
        "session_id": "1",
        "user_input": "API paracetamol",
        "current_form": {}
    }
    res_api = copilot_graph.invoke(state_api)
    # product_name, dosage_form should be set. 
    # API requires: product_name, batch_lot_number, dosage_form (3 total)
    assert res_api["completeness_pct"] == (2 / 3 * 100)
    assert "batch_lot_number" in res_api["missing_fields"]
    assert "affected_quantity" not in res_api["missing_fields"] # not required for API
    
    # FDF case
    state_fdf = {
        "session_id": "1",
        "user_input": "FDF amoxicillin",
        "current_form": {}
    }
    res_fdf = copilot_graph.invoke(state_fdf)
    # FDF requires: product_name, batch_lot_number, dosage_form, affected_quantity (4 total)
    # product and dosage_form set -> 2/4
    assert res_fdf["completeness_pct"] == 50.0
    assert "batch_lot_number" in res_fdf["missing_fields"]
    assert "affected_quantity" in res_fdf["missing_fields"]

def test_full_graph_state():
    """Test 5: Verify all expected major fields are present in the final state."""
    initial_state = {
        "session_id": "session_full",
        "user_input": "Product Paracetamol batch B123 dosage form API",
        "current_form": {}
    }
    
    result = copilot_graph.invoke(initial_state)
    
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
