from app.graph.state import CopilotState

# Configurable threshold for readiness (architecture constraint)
COMPLETENESS_READY_THRESHOLD_PCT = 100.0

def completeness_node(state: CopilotState) -> dict:
    """
    Completeness node for the AIVOA Copilot workflow.
    
    Inspects merged_form and calculates completeness_pct and missing_fields.
    Different required fields based on dosage_form (API vs FDF).
    """
    merged_form = state.get("merged_form", {})
    
    # Common complaint information across all dosage forms
    required_fields = [
        "complaint_source",
        "customer_name",
        "product_name",
        "batch_lot_number",
        "complaint_date",
        "complaint_type",
        "detailed_description",
        "dosage_form"
    ]
    
    # Form-specific required fields
    dosage_form = merged_form.get("dosage_form")
    if dosage_form == "FDF":
        # Finished Dosage Form typically requires quantity
        required_fields.append("affected_quantity")
    elif dosage_form == "API":
        # Active Pharmaceutical Ingredient
        required_fields.append("affected_quantity") # API also needs amount
        
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
