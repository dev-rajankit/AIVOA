from app.graph.state import CopilotState

def extraction_node(state: CopilotState) -> CopilotState:
    """
    Extraction node for the AIVOA Copilot workflow.
    
    In this mocked chunk, we deterministically extract fields based on keywords
    in the user_input. This proves the graph wires correctly to the merge node.
    """
    user_input = state.get("user_input", "").lower()
    
    extracted = {}
    
    # Mocking deterministic extraction rules
    if "paracetamol" in user_input:
        extracted["product_name"] = "Paracetamol"
    if "amoxicillin" in user_input:
        extracted["product_name"] = "Amoxicillin Capsules 500mg"
        
    if "b123" in user_input:
        extracted["batch_lot_number"] = "B123"
    elif "amx24601" in user_input:
        extracted["batch_lot_number"] = "AMX24601"
    elif "amx24602" in user_input:
        extracted["batch_lot_number"] = "AMX24602"
        
    if "fdf" in user_input or "capsules" in user_input or "tablets" in user_input:
        extracted["dosage_form"] = "FDF"
    elif "api" in user_input:
        extracted["dosage_form"] = "API"
        
    if "48 capsules" in user_input:
        extracted["affected_quantity"] = "48 capsules"
        
    return {
        "extracted_fields": extracted
    }
