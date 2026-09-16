from app.graph.state import CopilotState

def compose_response_node(state: CopilotState) -> CopilotState:
    """
    Compose response node for the AIVOA Copilot workflow.
    
    Generates a deterministic response without LLM calls for this chunk.
    """
    changed_fields = state.get("changed_fields", [])
    completeness_pct = state.get("completeness_pct", 0.0)
    intent = state.get("intent")
    
    if intent == "new_complaint":
        reply = "I have started logging the new complaint based on your input."
    else:
        reply = "I have updated the complaint information."
        
    if changed_fields:
        fields_str = ", ".join(changed_fields)
        reply += f" Updated fields: {fields_str}."
        
    reply += f" The form is currently {completeness_pct:.0f}% complete."
    
    return {
        "assistant_reply": reply
    }
