from app.graph.state import CopilotState

def risk_capa_node(state: CopilotState) -> CopilotState:
    """
    Risk and CAPA node for the AIVOA Copilot workflow.
    
    Returns a deterministic mock RiskAssessment.
    TODO: In future chunks, replace with LLM reasoning call (gpt-oss-120b).
    """
    merged_form = state.get("merged_form", {})
    
    # Simple deterministic rule for mock: if product_name is known, mock risk
    if merged_form.get("product_name"):
        risk_assessment = {
            "severity": "Major",
            "occurrence": 5,
            "detectability": 2,
            "rpn": 10,
            "recommended_action": "Route to QA investigation.",
            "root_cause_hint": "Potential manufacturing defect.",
            "capa_recommendation": "Review batch records.",
            "regulatory_flag": False,
            "ai_reasoning_summary": "Mocked reasoning for Chunk 4.",
            "model_used": "mocked"
        }
        return {"risk_assessment": risk_assessment}
        
    return {"risk_assessment": None}
