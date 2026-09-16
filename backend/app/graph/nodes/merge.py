from app.graph.state import CopilotState

def merge_node(state: CopilotState) -> CopilotState:
    """
    Merge node for the AIVOA Copilot workflow.
    
    Reconciles extracted_fields into current_form. Only fields that are not None
    in extracted_fields will overwrite existing fields.
    Records which fields actually changed.
    """
    current_form = state.get("current_form", {})
    extracted_fields = state.get("extracted_fields", {})
    
    merged = dict(current_form)
    changed = []
    
    for field, value in extracted_fields.items():
        if value is not None and value != merged.get(field):
            changed.append(field)
            merged[field] = value
            
    return {
        "merged_form": merged,
        "changed_fields": changed
    }
