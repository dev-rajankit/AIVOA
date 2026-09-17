from pydantic import BaseModel, EmailStr, Field

from app.schemas.complaint import ComplaintFields, RiskAssessment


class ReportRequest(BaseModel):
    """
    Request payload to generate a PDF report.
    Since the backend doesn't persist the complaint form state until Chunk 12,
    the frontend passes the current state to be rendered.
    """
    complaint_id: str = Field(..., description="The unique identifier for the complaint")
    complaint: ComplaintFields
    risk: RiskAssessment | None = None


class EmailReportRequest(ReportRequest):
    """
    Request payload to generate a PDF report and send it via email.
    """
    recipient_email: EmailStr = Field(..., description="The recipient's email address")
