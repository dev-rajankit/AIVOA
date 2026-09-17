import logging

from fastapi import APIRouter, Depends, HTTPException

from app.graph.graph import copilot_graph, build_production_graph
from app.graph.state import CopilotState
from app.schemas.complaint import CopilotMessageRequest, CopilotMessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Global variable to hold the compiled production graph
_prod_graph = None

def get_graph():
    """
    Dependency to provide the compiled graph.
    Compiles it lazily on the first request to avoid failing at import time
    if API keys aren't set during test collection.
    """
    global _prod_graph
    # If the graph was never built, or if it previously fell back to the mock graph, try to build it
    if _prod_graph is None or _prod_graph is copilot_graph:
        try:
            _prod_graph = build_production_graph()
            logger.info("Successfully built production graph.")
        except Exception as e:
            logger.error(f"Failed to build production graph: {e}")
            # Fallback to the mocked graph if production fails (e.g., missing API key)
            _prod_graph = copilot_graph
    return _prod_graph

@router.post("/message", response_model=CopilotMessageResponse, response_model_exclude_none=True)
async def process_copilot_message(
    request: CopilotMessageRequest,
    graph=Depends(get_graph),
):
    """
    Process a user message through the AIVOA Copilot workflow.
    
    This endpoint implements Phase 4 logic:
    - Parses the incoming message.
    - If `current_form` is provided, it uses it as the base state (for Tool 2 edits).
    - Invokes the LangGraph asynchronously.
    - Returns the resulting patch and assistant reply.
    """
    try:
        current_form_dict = request.current_form.model_dump(exclude_none=True) if request.current_form else {}
        
        # Construct the initial state
        initial_state = CopilotState(
            user_input=request.message,
            input_type=request.input_type,
            current_form=current_form_dict,
        )
        
        logger.info(f"Invoking graph for session {request.session_id}")
        
        # Invoke the graph asynchronously
        final_state = await graph.ainvoke(initial_state)
        
        # Transform state back to response
        # The frontend wants a form_patch (only fields that changed). 
        # But for the response contract, we provide the full extracted patch.
        # Actually, the requirement says form_patch should contain only changed fields.
        # Let's construct a patch of just the fields in changed_fields.
        
        changed_keys = final_state.get("changed_fields", [])
        merged = final_state.get("merged_form", {})
        patch_dict = {k: merged[k] for k in changed_keys if k in merged}
        
        form_patch = None
        if patch_dict:
            # We construct a ComplaintFields but it might fail if partial data is strictly validated.
            # But ComplaintFields is all Optional, so it should be fine.
            form_patch = patch_dict

        response = CopilotMessageResponse(
            assistant_reply=final_state.get("assistant_reply", ""),
            form_patch=form_patch,
            risk_patch=final_state.get("risk_assessment"),
            changed_fields=changed_keys,
            completeness_pct=final_state.get("completeness_pct", 0.0),
            missing_fields=final_state.get("missing_fields", []),
            intent=final_state.get("intent", "new_complaint"),
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing copilot message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
