"""
AIVOA — Canonical Pydantic Data Contracts

This module defines the single source of truth for complaint and risk
data shapes. Per the architecture spec (§5.2):

    "Define the complaint fields ONCE, as a Pydantic model, and derive
     three things from it:
       1. The Groq strict JSON schema (via .model_json_schema())
       2. The SQLAlchemy table column mapping
       3. The TypeScript/Redux shape the frontend expects"

Design principles:
- ALL complaint field definitions live here. No duplication.
- SQLAlchemy models (app/db/models.py) = database persistence layer.
  Pydantic schemas (this file) = validated application/AI contracts.
  These two must NOT inherit from each other.
- All fields on ComplaintFields are Optional because:
    1. AI extraction may only find some fields.
    2. Users provide information incrementally across turns.
    3. The merge_node needs to distinguish missing (None) from present.
- Enum/literal values are validated at the schema boundary.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# ComplaintFields — the ONE canonical complaint data shape (§5.2)
# =============================================================================


class ComplaintFields(BaseModel):
    """
    Canonical complaint field definitions.

    Used by:
    - Extraction LLM (via .model_json_schema() for strict structured output)
    - merge_node (partial patch: only non-None fields overwrite)
    - FastAPI response (form_patch in copilot response)
    - Frontend (drives the read-only complaint form)

    Every field is Optional because:
    - First extraction may only capture a subset.
    - Edit/correction turns only update specific fields.
    - The merge_node uses None to mean "no change" (preserve existing value).
    """

    complaint_source: str | None = Field(
        None, description="Email, Phone, Portal, Letter"
    )
    customer_name: str | None = None
    product_name: str | None = None
    product_strength_grade: str | None = None
    batch_lot_number: str | None = None
    affected_quantity: str | None = Field(
        None,
        description="Free text — e.g. '50 kg (2 HDPE Drums)' or '48 capsules'",
    )
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    dosage_form: Literal["API", "FDF"] | None = Field(
        None,
        description="API = Active Pharmaceutical Ingredient, FDF = Finished Dosage Form",
    )
    complaint_type: str | None = None
    complaint_date: date | None = None
    detailed_description: str | None = None

    model_config = {"extra": "forbid"}


# =============================================================================
# RiskAssessment — AI risk/CAPA classification (§4.2, §5.2)
# =============================================================================


class RiskAssessment(BaseModel):
    """
    AI-generated risk classification and CAPA recommendation.

    Severity is constrained to Minor/Major/Critical per the architecture spec.
    FMEA scores (occurrence, detectability) are optional bonus fields.
    RPN is an optional integer — computed by application logic (risk_capa_node),
    not at schema validation level.
    """

    severity: Literal["Minor", "Major", "Critical"]
    occurrence: int | None = Field(
        None, ge=1, le=10, description="FMEA occurrence score 1-10"
    )
    detectability: int | None = Field(
        None, ge=1, le=10, description="FMEA detectability score 1-10"
    )
    rpn: int | None = Field(
        None, description="Risk Priority Number — computed by risk_capa_node"
    )
    recommended_action: str | None = None
    root_cause_hint: str | None = Field(
        None,
        description="AI's 5-Whys/6M first guess — labeled as a hint, not a finding",
    )
    capa_recommendation: str | None = None
    regulatory_flag: bool = Field(
        False, description="True if complaint looks FAR-reportable"
    )
    ai_reasoning_summary: str | None = None
    model_used: str | None = Field(
        None, description="Which Groq model produced this assessment"
    )

    model_config = {"extra": "forbid"}


# =============================================================================
# ExtractionResult — structured LLM extraction output (§5.4)
# =============================================================================


class ExtractionResult(BaseModel):
    """
    The structured output returned by the extraction LLM.

    Reuses ComplaintFields directly — the extraction node's JSON schema
    is literally ComplaintFields.model_json_schema(). This is the key
    "one schema, three consumers, zero drift" principle from §5.2.
    """

    fields: ComplaintFields

    model_config = {"extra": "forbid"}


# =============================================================================
# Copilot API contracts — POST /api/copilot/message (§5.3)
# =============================================================================


class CopilotMessageRequest(BaseModel):
    """
    Request body for POST /api/copilot/message.

    Represents one user turn in the copilot conversation.
    """

    session_id: str = Field(
        ..., min_length=1, description="Groups messages into a conversation session"
    )
    complaint_id: str | None = Field(
        None, description="UUID of existing complaint, if editing"
    )
    message: str = Field(
        ..., min_length=1, description="The user's natural language input"
    )
    input_type: Literal["text", "document"] = Field(
        "text", description="Whether this is plain text or a document upload"
    )

    model_config = {"extra": "forbid"}


class CopilotMessageResponse(BaseModel):
    """
    Response body for POST /api/copilot/message.

    Shape defined by architecture spec §5.3:
        {assistant_reply, form_patch, risk_patch, changed_fields}

    form_patch uses ComplaintFields directly — since all its fields are
    Optional, it naturally represents a partial update (only non-None
    fields should be applied by the frontend/merge_node).
    """

    assistant_reply: str = Field(
        ..., description="The copilot's natural language response"
    )
    form_patch: ComplaintFields | None = Field(
        None,
        description="Partial complaint update — only non-None fields changed",
    )
    risk_patch: RiskAssessment | None = Field(
        None,
        description="Risk assessment update, if computed this turn",
    )
    changed_fields: list[str] = Field(
        default_factory=list,
        description="Field names that changed this turn — drives frontend highlighting",
    )

    model_config = {"extra": "forbid"}
