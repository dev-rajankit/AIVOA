import smtplib
from email.message import EmailMessage
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_report_email(pdf_bytes: bytes, recipient: str, complaint_id: str) -> None:
    """
    Send an email with the generated PDF report attached.
    Uses standard smtplib. If no SMTP_HOST is configured, it falls back to simply
    logging the email structure, preventing local dev failures if emails aren't set up.
    """
    msg = EmailMessage()
    msg['Subject'] = f"AIVOA Complaint Report — {complaint_id}"
    msg['From'] = getattr(settings, "SMTP_FROM", "aivoa@example.com")
    msg['To'] = recipient
    
    body = f"""Hello,

Please find the detailed AIVOA Complaint Report attached for complaint {complaint_id}.

This report contains:
- Processed complaint details
- Extracted structured data
- Risk Assessment and CAPA recommendations (if available)

Status: Pending Triage

Best regards,
AIVOA Automated System
"""
    msg.set_content(body)
    
    # Attach the PDF
    msg.add_attachment(
        pdf_bytes, 
        maintype='application', 
        subtype='pdf', 
        filename=f"AIVOA_{complaint_id}_report.pdf"
    )

    smtp_host = getattr(settings, "SMTP_HOST", None)
    
    if not smtp_host:
        logger.warning(
            "SMTP_HOST not configured. Email will not be sent over network. "
            f"Would have sent email to {recipient} with subject '{msg['Subject']}'."
        )
        return

    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    smtp_user = getattr(settings, "SMTP_USER", None)
    smtp_pass = getattr(settings, "SMTP_PASS", None)
    
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            # We assume STARTTLS if port is standard 587
            if smtp_port == 587:
                server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            logger.info(f"Successfully sent report email to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        raise RuntimeError(f"Email delivery failed: {e}")
