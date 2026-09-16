"""create core tables

Revision ID: 9e44e0450743
Revises:
Create Date: 2026-09-16 20:30:32.203753

Creates:
  - PostgreSQL enums: complaintstatus, dosageform, riskseverity, auditactor
  - Tables: complaints, risk_assessments, audit_log, copilot_messages
  - Indexes: batch_lot_number, session_id, audit_log(complaint_id, created_at)
  - Foreign keys with CASCADE delete
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9e44e0450743'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Enum types — created before tables, dropped after
complaintstatus = postgresql.ENUM(
    'pending_triage', 'ready_to_commit', 'under_investigation',
    'capa_in_progress', 'closed',
    name='complaintstatus', create_type=False,
)
dosageform = postgresql.ENUM('API', 'FDF', name='dosageform', create_type=False)
riskseverity = postgresql.ENUM('Minor', 'Major', 'Critical', name='riskseverity', create_type=False)
auditactor = postgresql.ENUM('AI_COPILOT', name='auditactor', create_type=False)


def upgrade() -> None:
    """Create all core tables, enums, indexes, and constraints."""

    # --- Create PostgreSQL enum types ---
    complaintstatus.create(op.get_bind(), checkfirst=True)
    dosageform.create(op.get_bind(), checkfirst=True)
    riskseverity.create(op.get_bind(), checkfirst=True)
    auditactor.create(op.get_bind(), checkfirst=True)

    # --- complaints ---
    op.create_table(
        'complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_number', sa.String(20), unique=True, nullable=False,
                   comment='Human-readable business ID, e.g. CC-2026-00154'),
        sa.Column('status', complaintstatus, nullable=False,
                   server_default='pending_triage'),
        sa.Column('dosage_form', dosageform, nullable=True),
        sa.Column('complaint_source', sa.Text(), nullable=True),
        sa.Column('customer_name', sa.Text(), nullable=True),
        sa.Column('product_name', sa.Text(), nullable=True),
        sa.Column('product_strength_grade', sa.Text(), nullable=True),
        sa.Column('batch_lot_number', sa.Text(), nullable=True,
                   comment='Indexed for duplicate detection queries'),
        sa.Column('affected_quantity', sa.Text(), nullable=True,
                   comment="Kept as text — e.g. '50 kg (2 HDPE Drums)'"),
        sa.Column('manufacturing_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('complaint_type', sa.Text(), nullable=True),
        sa.Column('complaint_date', sa.Date(), nullable=True),
        sa.Column('detailed_description', sa.Text(), nullable=True),
        sa.Column('raw_extraction_json', postgresql.JSONB(), nullable=True,
                   comment='Full LLM extraction payload for audit and re-processing'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                   server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                   server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_complaints_batch_lot_number', 'complaints', ['batch_lot_number'])

    # --- risk_assessments ---
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('severity', riskseverity, nullable=False),
        sa.Column('occurrence_score', sa.Integer(), nullable=True,
                   comment='FMEA occurrence score 1-10'),
        sa.Column('detectability_score', sa.Integer(), nullable=True,
                   comment='FMEA detectability score 1-10'),
        sa.Column('rpn', sa.Integer(), nullable=True,
                   comment='Risk Priority Number — computed by application logic, not DB'),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('root_cause_hint', sa.Text(), nullable=True,
                   comment="AI's 5-Whys/6M first guess — labeled as a hint, not a finding"),
        sa.Column('capa_recommendation', sa.Text(), nullable=True),
        sa.Column('regulatory_flag', sa.Boolean(), nullable=False, server_default='false',
                   comment='True if complaint looks FAR-reportable'),
        sa.Column('ai_reasoning_summary', sa.Text(), nullable=True,
                   comment='Short explanation of why the model produced this assessment'),
        sa.Column('model_used', sa.Text(), nullable=True,
                   comment='Which Groq model produced this — traceability'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                   server_default=sa.func.now(), nullable=False),
    )

    # --- audit_log ---
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('complaint_id', postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_name', sa.Text(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=False),
        sa.Column('changed_by', auditactor, nullable=False,
                   server_default='AI_COPILOT'),
        sa.Column('source_message', sa.Text(), nullable=True,
                   comment='The exact NL prompt that caused this change'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                   server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_log_complaint_created', 'audit_log',
                    ['complaint_id', 'created_at'])

    # --- copilot_messages ---
    op.create_table(
        'copilot_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(64), nullable=False,
                   comment='Groups messages into a conversation session'),
        sa.Column('role', sa.String(20), nullable=False,
                   comment="'user' or 'assistant'"),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                   server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_copilot_messages_session_id', 'copilot_messages', ['session_id'])


def downgrade() -> None:
    """Drop all core tables and enums."""
    op.drop_table('copilot_messages')
    op.drop_table('audit_log')
    op.drop_table('risk_assessments')
    op.drop_table('complaints')

    # Drop enum types after tables
    auditactor.drop(op.get_bind(), checkfirst=True)
    riskseverity.drop(op.get_bind(), checkfirst=True)
    dosageform.drop(op.get_bind(), checkfirst=True)
    complaintstatus.drop(op.get_bind(), checkfirst=True)
