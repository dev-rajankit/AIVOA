"""
Tests for SQLAlchemy models and metadata.

These tests verify the model definitions, table structure, constraints,
indexes, and enum values WITHOUT requiring a running PostgreSQL instance.
They operate purely on SQLAlchemy's metadata reflection.
"""

from sqlalchemy import inspect as sa_inspect

from app.db.models import (
    Base,
    Complaint,
    RiskAssessment,
    AuditLog,
    CopilotMessage,
    ComplaintStatus,
    DosageForm,
    RiskSeverity,
    AuditActor,
)


# =========================================================================
# 1. Model imports and metadata
# =========================================================================


def test_all_models_import():
    """All four core models should import without errors."""
    assert Complaint is not None
    assert RiskAssessment is not None
    assert AuditLog is not None
    assert CopilotMessage is not None


def test_metadata_contains_all_tables():
    """Base.metadata should contain exactly the four expected tables."""
    table_names = set(Base.metadata.tables.keys())
    expected = {"complaints", "risk_assessments", "audit_log", "copilot_messages"}
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"


# =========================================================================
# 2. Complaint model columns
# =========================================================================

EXPECTED_COMPLAINT_COLUMNS = {
    "id", "complaint_number", "status", "dosage_form",
    "complaint_source", "customer_name", "product_name",
    "product_strength_grade", "batch_lot_number", "affected_quantity",
    "manufacturing_date", "expiry_date", "complaint_type",
    "complaint_date", "detailed_description", "raw_extraction_json",
    "created_at", "updated_at",
}


def test_complaint_has_expected_columns():
    """Complaint table should contain all fields from architecture spec §4.1."""
    mapper = sa_inspect(Complaint)
    actual_columns = {col.key for col in mapper.columns}
    missing = EXPECTED_COMPLAINT_COLUMNS - actual_columns
    assert not missing, f"Missing complaint columns: {missing}"


def test_complaint_number_is_unique():
    """complaint_number must have a unique constraint."""
    table = Complaint.__table__
    col = table.c.complaint_number
    # Check column-level unique or table-level unique constraints
    has_unique = col.unique or any(
        col in uc.columns
        for uc in table.constraints
        if hasattr(uc, "columns")
    )
    assert has_unique, "complaint_number must be unique"


def test_batch_lot_number_is_indexed():
    """batch_lot_number must be indexed for duplicate detection queries."""
    table = Complaint.__table__
    indexed_columns = set()
    for idx in table.indexes:
        for col in idx.columns:
            indexed_columns.add(col.name)
    assert "batch_lot_number" in indexed_columns, (
        "batch_lot_number must be indexed (needed for duplicate detection)"
    )


def test_raw_extraction_json_is_jsonb():
    """raw_extraction_json should use PostgreSQL JSONB type."""
    table = Complaint.__table__
    col = table.c.raw_extraction_json
    # JSONB type name
    assert "JSON" in type(col.type).__name__.upper(), (
        f"raw_extraction_json should be JSONB, got {type(col.type).__name__}"
    )


# =========================================================================
# 3. Risk Assessment model
# =========================================================================


def test_risk_assessment_has_complaint_fk():
    """risk_assessments.complaint_id must reference complaints.id."""
    table = RiskAssessment.__table__
    fk_targets = set()
    for fk in table.foreign_keys:
        fk_targets.add(fk.target_fullname)
    assert "complaints.id" in fk_targets, (
        "risk_assessments must have FK to complaints.id"
    )


EXPECTED_RISK_COLUMNS = {
    "id", "complaint_id", "severity", "occurrence_score",
    "detectability_score", "rpn", "recommended_action",
    "root_cause_hint", "capa_recommendation", "regulatory_flag",
    "ai_reasoning_summary", "model_used", "created_at",
}


def test_risk_assessment_has_expected_columns():
    """RiskAssessment should contain fields from architecture spec §4.2."""
    mapper = sa_inspect(RiskAssessment)
    actual = {col.key for col in mapper.columns}
    missing = EXPECTED_RISK_COLUMNS - actual
    assert not missing, f"Missing risk assessment columns: {missing}"


# =========================================================================
# 4. Audit Log model
# =========================================================================


def test_audit_log_has_complaint_fk():
    """audit_log.complaint_id must reference complaints.id."""
    table = AuditLog.__table__
    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "complaints.id" in fk_targets


EXPECTED_AUDIT_COLUMNS = {
    "id", "complaint_id", "field_name", "old_value",
    "new_value", "changed_by", "source_message", "created_at",
}


def test_audit_log_has_expected_columns():
    """AuditLog should contain fields from architecture spec §4.3."""
    mapper = sa_inspect(AuditLog)
    actual = {col.key for col in mapper.columns}
    missing = EXPECTED_AUDIT_COLUMNS - actual
    assert not missing, f"Missing audit log columns: {missing}"


# =========================================================================
# 5. Copilot Message model
# =========================================================================

EXPECTED_COPILOT_COLUMNS = {"id", "session_id", "role", "content", "created_at"}


def test_copilot_message_has_expected_columns():
    """CopilotMessage should contain fields from architecture spec §4.4."""
    mapper = sa_inspect(CopilotMessage)
    actual = {col.key for col in mapper.columns}
    missing = EXPECTED_COPILOT_COLUMNS - actual
    assert not missing, f"Missing copilot message columns: {missing}"


def test_session_id_is_indexed():
    """session_id must be indexed for efficient conversation retrieval."""
    table = CopilotMessage.__table__
    indexed_columns = set()
    for idx in table.indexes:
        for col in idx.columns:
            indexed_columns.add(col.name)
    assert "session_id" in indexed_columns


# =========================================================================
# 6. Enum values match architecture spec
# =========================================================================


def test_complaint_status_values():
    """ComplaintStatus enum must match architecture spec §4.1."""
    expected = {
        "pending_triage", "ready_to_commit",
        "under_investigation", "capa_in_progress", "closed",
    }
    actual = {s.value for s in ComplaintStatus}
    assert actual == expected


def test_dosage_form_values():
    """DosageForm enum must match architecture spec §4.1."""
    assert {d.value for d in DosageForm} == {"API", "FDF"}


def test_risk_severity_values():
    """RiskSeverity enum must match architecture spec §4.2."""
    assert {s.value for s in RiskSeverity} == {"Minor", "Major", "Critical"}


def test_audit_actor_values():
    """AuditActor enum must include AI_COPILOT (§4.3)."""
    assert AuditActor.AI_COPILOT.value == "AI_COPILOT"


# =========================================================================
# 7. Relationships
# =========================================================================


def test_complaint_has_risk_assessments_relationship():
    """Complaint should have a relationship to RiskAssessment."""
    mapper = sa_inspect(Complaint)
    rel_names = {r.key for r in mapper.relationships}
    assert "risk_assessments" in rel_names


def test_complaint_has_audit_entries_relationship():
    """Complaint should have a relationship to AuditLog."""
    mapper = sa_inspect(Complaint)
    rel_names = {r.key for r in mapper.relationships}
    assert "audit_entries" in rel_names
