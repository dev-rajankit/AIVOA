from app.graph.state import CopilotState

def completeness_node(state: CopilotState) -> CopilotState:
    """
    Completeness node for the AIVOA Copilot workflow.
    
    Inspects merged_form and calculates completeness_pct and missing_fields.
    """
    merged_form = state.get("merged_form", {})
    
    # Base required fields
    required_fields = ["product_name", "batch_lot_number", "dosage_form"]
    
    # Branching based on dosage_form
    if merged_form.get("dosage_form") == "FDF":
        required_fields.append("affected_quantity")
        
    missing = []
    for field in required_fields:
        if not merged_form.get(field):
            missing.append(field)
            
    total = len(required_fields)
    present = total - len(missing)
    completeness_pct = (present / total * 100) if total > 0 else 0.0
    
    return {
        "completeness_pct": completeness_pct,
        "missing_fields": missing
    }
