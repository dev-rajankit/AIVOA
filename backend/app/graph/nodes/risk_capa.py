from app.graph.state import CopilotState
from app.core.config import settings

def risk_capa_node(state: CopilotState) -> CopilotState:
    """
    Risk and CAPA node for the AIVOA Copilot workflow.
    
    Implements a deterministic, rule-based mapping to calculate:
    - Severity (1-10)
    - Occurrence (1-10)
    - Detection (1-10)
    - RPN (S * O * D)
    - Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
    - Corrective and Preventive Actions (CAPA)
    """
    merged_form = state.get("merged_form", {})
    duplicate_status = state.get("duplicate_status", "UNIQUE")
    
    # Text block to search for keywords
    text_corpus = (
        str(merged_form.get("detailed_description", "")) + " " +
        str(merged_form.get("complaint_type", "")) + " " +
        str(merged_form.get("product_name", ""))
    ).lower()

    if not merged_form.get("product_name") and not merged_form.get("detailed_description"):
        # Not enough info yet to calculate risk
        return {"risk_assessment": None}

    # 1. Severity (S)
    safety_keywords = ["braking", "safety", "fire", "injury", "death", "hospital", "loss of control", "leak", "toxic", "critical"]
    is_safety_related = any(kw in text_corpus for kw in safety_keywords)
    severity_score = 9 if is_safety_related else 5
    if severity_score >= 8:
        severity = "Critical"
    elif severity_score >= 5:
        severity = "Major"
    else:
        severity = "Minor"

    # 2. Occurrence (O)
    if duplicate_status == "DUPLICATE":
        occurrence_score = 8
    elif duplicate_status == "POSSIBLE_DUPLICATE":
        occurrence_score = 5
    else:
        occurrence_score = 3

    # 3. Detection (D) - Higher means harder to detect
    hidden_keywords = ["intermittent", "latent", "hidden", "internal", "inside", "invisible"]
    obvious_keywords = ["visible", "obvious", "broken", "scratch", "color", "discolored", "smell"]
    
    if any(kw in text_corpus for kw in hidden_keywords):
        detection_score = 8
    elif any(kw in text_corpus for kw in obvious_keywords):
        detection_score = 2
    else:
        detection_score = 5

    # 4. RPN Calculation
    rpn = severity_score * occurrence_score * detection_score

    # 5. Risk Level
    if rpn >= settings.RPN_CRITICAL_THRESHOLD:
        risk_level = "CRITICAL"
    elif rpn >= settings.RPN_HIGH_THRESHOLD:
        risk_level = "HIGH"
    elif rpn >= settings.RPN_MEDIUM_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # 6. CAPA Generation
    if is_safety_related:
        corrective_action = "Inspect affected vehicles/components and identify the failure source immediately. Quarantine affected batches."
        preventive_action = "Review the relevant failure mode, strengthen inspection/testing controls, and evaluate a potential recall or safety bulletin."
        root_cause_hint = "Potential safety-critical component failure or severe manufacturing deviation."
        regulatory_flag = True
    else:
        corrective_action = "Inspect affected component and resolve the reported failure."
        preventive_action = "Review recurring failure patterns and evaluate process/product improvements."
        root_cause_hint = "Standard wear-and-tear or minor manufacturing defect."
        regulatory_flag = False

    risk_assessment = {
        "severity": severity,
        "severity_score": severity_score,
        "occurrence": occurrence_score,
        "detectability": detection_score,
        "rpn": rpn,
        "risk_level": risk_level,
        "corrective_action": corrective_action,
        "preventive_action": preventive_action,
        "capa_recommendation": f"{corrective_action} {preventive_action}",
        "root_cause_hint": root_cause_hint,
        "regulatory_flag": regulatory_flag,
        "ai_reasoning_summary": "Calculated using deterministic rule-based mapping.",
        "model_used": "deterministic-rules-engine"
    }

    return {"risk_assessment": risk_assessment}
