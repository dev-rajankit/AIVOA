from app.graph.state import CopilotState

def router_node(state: CopilotState) -> CopilotState:
    """
    Router node for the AIVOA Copilot workflow.
    
    Determines the intent and input_type deterministically for this mock chunk.
    If current_form is empty -> new_complaint.
    If current_form has data -> edit_complaint.
    """
    current_form = state.get("current_form", {})
    
    # Simple deterministic routing based on whether a form already exists
    if not current_form:
        intent = "new_complaint"
    else:
        intent = "edit_complaint"
        
    # Defaulting input type to text for the mock
    input_type = state.get("input_type", "text")
    
    return {
        "intent": intent,
        "input_type": input_type
    }
