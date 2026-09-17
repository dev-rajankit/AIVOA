from app.graph.state import CopilotState

def router_node(state: CopilotState) -> dict:
    """
    Router node for the AIVOA Copilot workflow.
    
    Determines the intent and input_type deterministically.
    - If current_form is empty -> new_complaint.
    - If current_form has data -> inspect user_input for correction keywords.
      If keywords found, edit_complaint. Else fallback to chit_chat.
    """
    current_form = state.get("current_form", {})
    user_input = state.get("user_input", "").lower()
    
    if not current_form:
        intent = "new_complaint"
    else:
        # Lightweight heuristic for edit_complaint
        correction_keywords = [
            "correct", "change", "update", "sorry", "actually", 
            "wrong", "replace", "is", "should be"
        ]
        
        is_edit = any(kw in user_input for kw in correction_keywords)
        if is_edit:
            intent = "edit_complaint"
        else:
            intent = "chit_chat"
            
    # Defaulting input type to text
    input_type = state.get("input_type", "text")
    
    return {
        "intent": intent,
        "input_type": input_type
    }
