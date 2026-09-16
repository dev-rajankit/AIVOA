"""
AIVOA Pydantic Schemas — Public API

Import the canonical data contracts from here:
    from app.schemas import ComplaintFields, RiskAssessment, ...
"""

from app.schemas.complaint import (
    ComplaintFields,
    CopilotMessageRequest,
    CopilotMessageResponse,
    ExtractionResult,
    RiskAssessment,
)

__all__ = [
    "ComplaintFields",
    "RiskAssessment",
    "ExtractionResult",
    "CopilotMessageRequest",
    "CopilotMessageResponse",
]
