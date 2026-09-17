import logging

from fastapi import APIRouter, Depends, HTTPException

from app.graph.graph import copilot_graph, build_production_graph
from app.graph.state import CopilotState
from app.schemas.complaint import CopilotMessageRequest, CopilotMessageResponse

import uuid
from datetime import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Complaint, RiskAssessment, AuditLog, CopilotMessage, ComplaintStatus, DosageForm, DuplicateStatus, AuditActor

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
    db: AsyncSession = Depends(get_db),
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
            duplicate_status=final_state.get("duplicate_status", "UNIQUE"),
            duplicate_matches=final_state.get("duplicate_matches", []),
            complaint_id=None,
        )

        # --- Persistence Layer ---
        # 1. Resolve or Create Complaint
        complaint = None
        if request.complaint_id:
            try:
                cid = uuid.UUID(request.complaint_id)
                result = await db.execute(select(Complaint).where(Complaint.id == cid))
                complaint = result.scalar_one_or_none()
            except ValueError:
                pass
        
        if not complaint:
            # Generate a simple unique complaint number
            now_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            cnum = f"CC-{now_str}-{random.randint(100, 999)}"
            complaint = Complaint(
                complaint_number=cnum,
                status=ComplaintStatus.pending_triage
            )
            db.add(complaint)
            await db.flush() # To get the ID
        
        response.complaint_id = str(complaint.id)

        # 2. Update Complaint Fields
        for k, v in merged.items():
            if hasattr(complaint, k) and k not in ["dosage_form"]:
                setattr(complaint, k, v)
        
        if "dosage_form" in merged and merged["dosage_form"]:
            complaint.dosage_form = DosageForm(merged["dosage_form"])

        if final_state.get("duplicate_status"):
            complaint.duplicate_status = DuplicateStatus(final_state["duplicate_status"])
        
        matches = final_state.get("duplicate_matches", [])
        if matches and len(matches) > 0:
            try:
                complaint.matched_complaint_id = uuid.UUID(matches[0]["matched_complaint_id"])
            except Exception:
                pass
        
        # 3. Persist Risk Assessment if present
        risk_data = final_state.get("risk_assessment")
        if risk_data:
            risk_record = RiskAssessment(
                complaint_id=complaint.id,
                severity=risk_data.get("severity"),
                severity_score=risk_data.get("severity_score"),
                risk_level=risk_data.get("risk_level"),
                occurrence_score=risk_data.get("occurrence"),
                detectability_score=risk_data.get("detectability"),
                rpn=risk_data.get("rpn"),
                recommended_action=risk_data.get("recommended_action"),
                root_cause_hint=risk_data.get("root_cause_hint"),
                corrective_action=risk_data.get("corrective_action"),
                preventive_action=risk_data.get("preventive_action"),
                capa_recommendation=risk_data.get("capa_recommendation"),
                regulatory_flag=risk_data.get("regulatory_flag", False),
                ai_reasoning_summary=risk_data.get("ai_reasoning_summary"),
                model_used=risk_data.get("model_used")
            )
            db.add(risk_record)
            
        # 4. Persist Audit Logs for changed fields
        current_dict = current_form_dict
        for field in changed_keys:
            old_val = current_dict.get(field)
            new_val = merged.get(field)
            
            # Convert values to string for audit log, or ignore if missing
            if new_val is not None:
                audit = AuditLog(
                    complaint_id=complaint.id,
                    field_name=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val),
                    changed_by=AuditActor.AI_COPILOT,
                    source_message=request.message
                )
                db.add(audit)
                
        # 5. Persist Chat History
        user_msg = CopilotMessage(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        asst_msg = CopilotMessage(
            session_id=request.session_id,
            role="assistant",
            content=response.assistant_reply
        )
        db.add(user_msg)
        db.add(asst_msg)
        
        await db.commit()
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing copilot message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
