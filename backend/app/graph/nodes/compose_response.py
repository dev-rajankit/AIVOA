from app.graph.state import CopilotState

def compose_response_node(state: CopilotState) -> dict:
    """
    Compose response node for the AIVOA Copilot workflow.
    
    Generates a deterministic response without LLM calls for this chunk.
    For edits, it states clearly what was updated.
    """
    changed_fields = state.get("changed_fields", [])
    intent = state.get("intent")
    
    if intent == "new_complaint":
        reply = "I have extracted the new complaint information."
    elif intent == "edit_complaint":
        if changed_fields:
            # Create a readable list of modified fields
            formatted_fields = [f.replace("_", " ").title() for f in changed_fields]
            fields_str = ", ".join(formatted_fields)
            reply = f"I've applied the updates to {fields_str}. The remaining complaint information was preserved."
        else:
            reply = "No changes were detected from your input."
    else:
        reply = "I am a complaint management assistant. Please provide complaint details or corrections."
    
    return {
        "assistant_reply": reply
    }
