from typing import Literal, Optional, TypedDict

class CopilotState(TypedDict):
    """
    LangGraph state for the AIVOA Copilot workflow.
    
    This represents the temporary working memory for one workflow execution.
    It is not the persistent database.
    """
    session_id: str
    complaint_id: Optional[str]
    user_input: str
    input_type: Literal["text", "document"]
    intent: Optional[Literal["new_complaint", "edit_complaint", "chit_chat"]]
    current_form: dict          # form state BEFORE this turn
    extracted_fields: dict      # raw LLM output THIS turn (matches ComplaintFields)
    merged_form: dict           # reconciled result (matches ComplaintFields)
    changed_fields: list[str]   # for FE highlighting + audit log
    completeness_pct: float
    missing_fields: list[str]
    duplicate_status: Literal["UNIQUE", "POSSIBLE_DUPLICATE", "DUPLICATE"]
    duplicate_matches: list[dict]
    risk_assessment: dict       # matches RiskAssessment schema
    assistant_reply: str
