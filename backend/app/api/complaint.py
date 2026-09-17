import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import Complaint, AuditLog
from app.schemas.complaint import ComplaintResponse, AuditLogResponse, ComplaintFields, RiskAssessment

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{complaint_id}", response_model=ComplaintResponse, response_model_exclude_none=True)
async def get_complaint(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a persisted complaint by ID, including its risk assessments.
    """
    try:
        cid = uuid.UUID(complaint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.risk_assessments))
        .where(Complaint.id == cid)
    )
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Serialize fields
    fields = ComplaintFields(
        complaint_source=complaint.complaint_source,
        customer_name=complaint.customer_name,
        product_name=complaint.product_name,
        product_strength_grade=complaint.product_strength_grade,
        batch_lot_number=complaint.batch_lot_number,
        affected_quantity=complaint.affected_quantity,
        manufacturing_date=complaint.manufacturing_date,
        expiry_date=complaint.expiry_date,
        dosage_form=complaint.dosage_form.value if complaint.dosage_form else None,
        complaint_type=complaint.complaint_type,
        complaint_date=complaint.complaint_date,
        detailed_description=complaint.detailed_description,
    )
    
    risk_assessments = []
    for ra in complaint.risk_assessments:
        risk_assessments.append(RiskAssessment(
            severity=ra.severity,
            severity_score=ra.severity_score,
            occurrence=ra.occurrence_score,
            detectability=ra.detectability_score,
            rpn=ra.rpn,
            recommended_action=ra.recommended_action,
            root_cause_hint=ra.root_cause_hint,
            risk_level=ra.risk_level,
            corrective_action=ra.corrective_action,
            preventive_action=ra.preventive_action,
            capa_recommendation=ra.capa_recommendation,
            regulatory_flag=ra.regulatory_flag,
            ai_reasoning_summary=ra.ai_reasoning_summary,
            model_used=ra.model_used
        ))

    return ComplaintResponse(
        id=str(complaint.id),
        complaint_number=complaint.complaint_number,
        status=complaint.status.value,
        created_at=complaint.created_at.isoformat() if hasattr(complaint.created_at, "isoformat") else str(complaint.created_at),
        updated_at=complaint.updated_at.isoformat() if hasattr(complaint.updated_at, "isoformat") else str(complaint.updated_at),
        fields=fields,
        risk_assessments=risk_assessments,
        duplicate_status=complaint.duplicate_status.value,
        matched_complaint_id=str(complaint.matched_complaint_id) if complaint.matched_complaint_id else None
    )

@router.get("/{complaint_id}/audit", response_model=list[AuditLogResponse])
async def get_complaint_audit_log(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the chronological audit events for a complaint.
    """
    try:
        cid = uuid.UUID(complaint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.complaint_id == cid)
        .order_by(AuditLog.created_at.asc())
    )
    audit_logs = result.scalars().all()
    
    response = []
    for log in audit_logs:
        response.append(AuditLogResponse(
            id=str(log.id),
            field_name=log.field_name,
            old_value=log.old_value,
            new_value=log.new_value,
            changed_by=log.changed_by.value,
            source_message=log.source_message,
            created_at=log.created_at.isoformat() if hasattr(log.created_at, "isoformat") else str(log.created_at)
        ))
        
    return response
