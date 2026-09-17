"""
AIVOA — SQLAlchemy ORM Models

All four core database tables defined per the architecture spec (§4):

  1. complaints       — the central complaint record
  2. risk_assessments — AI-generated risk/CAPA assessment (1:many for versioning)
  3. audit_log        — 21 CFR Part 11 change tracking
  4. copilot_messages — multi-turn chat history

Design decisions:
- UUID primary keys: globally unique, safe for distributed systems, no
  sequential-ID enumeration risk. Complaint records may eventually be
  shared across facilities/tenants.
- complaint_number: separate human-readable business identifier (CC-2026-00154).
  Decoupled from the PK so it can follow business formatting rules without
  constraining the database.
- JSONB for raw_extraction_json: stores the exact LLM output for every
  complaint, enabling debugging and re-processing without re-calling the LLM.
  PostgreSQL-native JSONB supports indexing and querying if needed later.
- Enums defined as Python enums + PostgreSQL native enums: type-safe in both
  Python and the database, preventing invalid values at both layers.
- All timestamps use timezone-aware UTC (server_default=func.now()).
"""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Integer,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


# =============================================================================
# Enums — reusable across models, matching architecture spec exactly
# =============================================================================


class ComplaintStatus(str, enum.Enum):
    """Complaint lifecycle states (§2.3 of architecture spec)."""
    pending_triage = "pending_triage"
    ready_to_commit = "ready_to_commit"
    under_investigation = "under_investigation"
    capa_in_progress = "capa_in_progress"
    closed = "closed"


class DosageForm(str, enum.Enum):
    """Product type — drives completeness rules (§2.1)."""
    API = "API"   # Active Pharmaceutical Ingredient
    FDF = "FDF"   # Finished Dosage Form


class RiskSeverity(str, enum.Enum):
    """Risk classification levels (§4.2)."""
    Minor = "Minor"
    Major = "Major"
    Critical = "Critical"


class AuditActor(str, enum.Enum):
    """Who made the change — AI_COPILOT only in Round 1 (§4.3)."""
    AI_COPILOT = "AI_COPILOT"


class DuplicateStatus(str, enum.Enum):
    """Duplicate detection classification."""
    UNIQUE = "UNIQUE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    DUPLICATE = "DUPLICATE"


# =============================================================================
# Declarative Base
# =============================================================================


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all AIVOA models."""
    pass


# =============================================================================
# Complaint Model (§4.1)
# =============================================================================


class Complaint(Base):
    """
    Central complaint record.

    Each row represents one pharmaceutical customer complaint, with fields
    populated by the AI Copilot (never manually in Round 1). The
    raw_extraction_json column preserves the exact LLM output for
    audit/debug purposes.
    """

    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False,
        comment="Human-readable business ID, e.g. CC-2026-00154"
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaintstatus", create_constraint=True),
        nullable=False,
        default=ComplaintStatus.pending_triage,
    )
    dosage_form: Mapped[DosageForm | None] = mapped_column(
        Enum(DosageForm, name="dosageform", create_constraint=True),
        nullable=True,
    )

    # --- Complaint details (all nullable during intake) ---
    complaint_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_strength_grade: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_lot_number: Mapped[str | None] = mapped_column(
        Text, nullable=True, index=True,
        comment="Indexed for duplicate detection queries"
    )
    affected_quantity: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Kept as text — e.g. '50 kg (2 HDPE Drums)'"
    )
    manufacturing_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    complaint_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    complaint_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    detailed_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- LLM audit/debug ---
    raw_extraction_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Full LLM extraction payload for audit and re-processing"
    )

    # --- Duplicate Detection ---
    embedding = mapped_column(
        Vector(384), nullable=True,
        comment="all-MiniLM-L6-v2 vector for duplicate detection"
    )
    duplicate_status: Mapped[DuplicateStatus] = mapped_column(
        Enum(DuplicateStatus, name="duplicatestatus", create_constraint=True),
        nullable=False,
        default=DuplicateStatus.UNIQUE,
    )
    matched_complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=True,
        comment="ID of the best matching historical complaint, if any"
    )

    # --- Timestamps ---
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    audit_entries: Mapped[list["AuditLog"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )


# =============================================================================
# Risk Assessment Model (§4.2)
# =============================================================================


class RiskAssessment(Base):
    """
    AI-generated risk and CAPA assessment for a complaint.

    Stored as separate rows (not 1:1 overwrite) so assessment history
    is preserved — each re-run of the risk_capa_node produces a new row,
    enabling comparison of how the assessment changed as more complaint
    information was provided.
    """

    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, name="riskseverity", create_constraint=True),
        nullable=False,
    )
    occurrence_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="FMEA occurrence score 1-10"
    )
    detectability_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="FMEA detectability score 1-10"
    )
    rpn: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Risk Priority Number — computed by application logic, not DB"
    )
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_hint: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="AI's 5-Whys/6M first guess — labeled as a hint, not a finding"
    )
    capa_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulatory_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="True if complaint looks FAR-reportable"
    )
    ai_reasoning_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Short explanation of why the model produced this assessment"
    )
    model_used: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Which Groq model produced this — traceability"
    )

    # --- Timestamps ---
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    complaint: Mapped["Complaint"] = relationship(back_populates="risk_assessments")


# =============================================================================
# Audit Log Model (§4.3) — 21 CFR Part 11 compliance story
# =============================================================================


class AuditLog(Base):
    """
    Immutable audit trail for every AI-driven field change.

    Every field the merge_node changes gets one row here. This also
    powers the frontend's blue-highlight "diff" effect — the frontend
    asks "what changed in this turn?" and highlights those field IDs.
    """

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[AuditActor] = mapped_column(
        Enum(AuditActor, name="auditactor", create_constraint=True),
        nullable=False,
        default=AuditActor.AI_COPILOT,
    )
    source_message: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="The exact NL prompt that caused this change"
    )

    # --- Timestamps ---
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationships ---
    complaint: Mapped["Complaint"] = relationship(back_populates="audit_entries")


# =============================================================================
# Copilot Message Model (§4.4)
# =============================================================================


class CopilotMessage(Base):
    """
    Chat history for the AI Copilot.

    Persists conversation so a page refresh doesn't lose context.
    Needed because the agent is explicitly multi-turn (log → correct).
    """

    __tablename__ = "copilot_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="Groups messages into a conversation session"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="'user' or 'assistant'"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Timestamps ---
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# =============================================================================
# Additional Indexes
# =============================================================================

# Composite index for audit log queries by complaint + time
Index("ix_audit_log_complaint_created", AuditLog.complaint_id, AuditLog.created_at)
