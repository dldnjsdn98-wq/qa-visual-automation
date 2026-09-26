"""phase2 upload receipts

Revision ID: 0003_phase2_upload_receipts
Revises: 0002_phase1_domain
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_phase2_upload_receipts"
down_revision = "0002_phase1_domain"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_screenshots_project_id_id_client_upload_id",
        "screenshots",
        ["project_id", "id", "client_upload_id"],
    )
    op.create_check_constraint(
        "ck_screenshot_source_client_upload",
        "screenshots",
        "(source = 'manual' AND client_upload_id IS NULL) OR (source IN ('agent','automation') AND client_upload_id IS NOT NULL)",
        postgresql_not_valid=True,
    )
    op.execute("ALTER TABLE screenshots VALIDATE CONSTRAINT ck_screenshot_source_client_upload")
    op.create_index(
        "uq_screenshots_project_client_upload_id",
        "screenshots",
        ["project_id", "client_upload_id"],
        unique=True,
        postgresql_where=sa.text("client_upload_id IS NOT NULL"),
    )

    op.create_table(
        "upload_receipts",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("client_upload_id", sa.UUID(), nullable=False),
        sa.Column("fingerprint_version", sa.Integer(), nullable=False),
        sa.Column("upload_protocol_version", sa.Integer(), nullable=False),
        sa.Column("request_fingerprint", sa.CHAR(length=64), nullable=False),
        sa.Column("canonical_request", sa.LargeBinary(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("attempt_generation", sa.BigInteger(), nullable=False),
        sa.Column("attempt_token", sa.UUID(), nullable=False),
        sa.Column("candidate_screenshot_id", sa.UUID(), nullable=False),
        sa.Column("candidate_storage_key", sa.Text(), nullable=False),
        sa.Column("screenshot_id", sa.UUID(), nullable=True),
        sa.Column("lease_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.PrimaryKeyConstraint("project_id", "client_upload_id"),
        sa.UniqueConstraint("candidate_storage_key", name="uq_upload_receipts_candidate_storage_key"),
        sa.UniqueConstraint("screenshot_id", name="uq_upload_receipts_screenshot_id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT", name="fk_upload_receipts_project"),
        sa.ForeignKeyConstraint(["project_id", "screenshot_id"], ["screenshots.project_id", "screenshots.id"], ondelete="RESTRICT", name="fk_upload_receipts_project_screenshot"),
        sa.ForeignKeyConstraint(["project_id", "screenshot_id", "client_upload_id"], ["screenshots.project_id", "screenshots.id", "screenshots.client_upload_id"], ondelete="RESTRICT", deferrable=True, initially="DEFERRED", name="fk_upload_receipts_completed_identity"),
        sa.CheckConstraint("fingerprint_version = 1 AND upload_protocol_version = 1", name="ck_upload_receipt_versions"),
        sa.CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_upload_receipt_fingerprint"),
        sa.CheckConstraint("octet_length(canonical_request) BETWEEN 1 AND 65536", name="ck_upload_receipt_canonical_size"),
        sa.CheckConstraint("state IN ('PROCESSING','COMPLETED','FAILED')", name="ck_upload_receipt_state"),
        sa.CheckConstraint("attempt_generation >= 1", name="ck_upload_receipt_generation"),
        sa.CheckConstraint("substring(client_upload_id::text from 15 for 1) = '4' AND substring(client_upload_id::text from 20 for 1) IN ('8','9','a','b')", name="ck_upload_receipt_client_uuid4"),
        sa.CheckConstraint("substring(attempt_token::text from 15 for 1) = '4' AND substring(attempt_token::text from 20 for 1) IN ('8','9','a','b')", name="ck_upload_receipt_token_uuid4"),
        sa.CheckConstraint("candidate_storage_key IN ('objects/' || project_id::text || '/' || candidate_screenshot_id::text || '.png', 'objects/' || project_id::text || '/' || candidate_screenshot_id::text || '.jpg')", name="ck_upload_receipt_candidate_key"),
        sa.CheckConstraint("(state = 'PROCESSING' AND screenshot_id IS NULL AND lease_expires_at IS NOT NULL) OR (state = 'FAILED' AND screenshot_id IS NULL AND lease_expires_at IS NULL) OR (state = 'COMPLETED' AND screenshot_id = candidate_screenshot_id AND lease_expires_at IS NULL AND last_error_code IS NULL)", name="ck_upload_receipt_state_shape"),
        sa.CheckConstraint("last_error_code IS NULL OR last_error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'", name="ck_upload_receipt_error_code"),
    )
    op.create_index("ix_upload_receipts_processing_lease_expires_at", "upload_receipts", ["lease_expires_at"], postgresql_where=sa.text("state = 'PROCESSING'"))
    op.create_index("ix_upload_receipts_project_id", "upload_receipts", ["project_id"])
    # Keep the Phase 1 check in place until the replacement has validated.
    op.drop_constraint("ck_screenshot_phase1", "screenshots", type_="check")


def downgrade():
    op.drop_index("ix_upload_receipts_project_id", table_name="upload_receipts")
    op.drop_index("ix_upload_receipts_processing_lease_expires_at", table_name="upload_receipts")
    op.drop_table("upload_receipts")
    op.drop_index("uq_screenshots_project_client_upload_id", table_name="screenshots")
    op.drop_constraint("ck_screenshot_source_client_upload", "screenshots", type_="check")
    op.create_check_constraint("ck_screenshot_phase1", "screenshots", "source = 'manual' AND client_upload_id IS NULL")
    op.drop_constraint("uq_screenshots_project_id_id_client_upload_id", "screenshots", type_="unique")
