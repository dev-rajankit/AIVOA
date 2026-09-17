from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import logging

from app.schemas.report import ReportRequest, EmailReportRequest
from app.services.pdf_report import generate_complaint_pdf
from app.services.email_delivery import send_report_email

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/pdf")
async def generate_pdf(request: ReportRequest):
    """
    Generate a PDF report for a complaint based on the provided state.
    """
    try:
        pdf_bytes = generate_complaint_pdf(request)
        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="AIVOA_{request.complaint_id}_report.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")


@router.post("/email")
async def email_report(request: EmailReportRequest):
    """
    Generate a PDF report and send it to the specified email address.
    """
    try:
        pdf_bytes = generate_complaint_pdf(request)
    except Exception as e:
        logger.error(f"Error generating PDF report for email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    try:
        send_report_email(pdf_bytes, request.recipient_email, request.complaint_id)
        return {"status": "success", "message": f"Email successfully sent to {request.recipient_email}"}
    except RuntimeError as e:
        # Expected error from email service if SMTP fails
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send email")
