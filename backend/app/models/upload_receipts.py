from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, Integer, LargeBinary, PrimaryKeyConstraint, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import CHAR, TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class UploadReceipt(Base):
    __tablename__ = "upload_receipts"
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "client_upload_id"),
        UniqueConstraint("candidate_storage_key", name="uq_upload_receipts_candidate_storage_key"),
        UniqueConstraint("screenshot_id", name="uq_upload_receipts_screenshot_id"),
        ForeignKeyConstraint(
            ["project_id", "screenshot_id"],
            ["screenshots.project_id", "screenshots.id"],
            ondelete="RESTRICT",
            name="fk_upload_receipts_project_screenshot",
        ),
        ForeignKeyConstraint(
            ["project_id", "screenshot_id", "client_upload_id"],
            ["screenshots.project_id", "screenshots.id", "screenshots.client_upload_id"],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            name="fk_upload_receipts_completed_identity",
        ),
        CheckConstraint("fingerprint_version = 1 AND upload_protocol_version = 1", name="ck_upload_receipt_versions"),
        CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_upload_receipt_fingerprint"),
        CheckConstraint("octet_length(canonical_request) BETWEEN 1 AND 65536", name="ck_upload_receipt_canonical_size"),
        CheckConstraint("state IN ('PROCESSING','COMPLETED','FAILED')", name="ck_upload_receipt_state"),
        CheckConstraint("attempt_generation >= 1", name="ck_upload_receipt_generation"),
        CheckConstraint("substring(client_upload_id::text from 15 for 1) = '4' AND substring(client_upload_id::text from 20 for 1) IN ('8','9','a','b')", name="ck_upload_receipt_client_uuid4"),
        CheckConstraint("substring(attempt_token::text from 15 for 1) = '4' AND substring(attempt_token::text from 20 for 1) IN ('8','9','a','b')", name="ck_upload_receipt_token_uuid4"),
        CheckConstraint("candidate_storage_key IN ('objects/' || project_id::text || '/' || candidate_screenshot_id::text || '.png', 'objects/' || project_id::text || '/' || candidate_screenshot_id::text || '.jpg')", name="ck_upload_receipt_candidate_key"),
        CheckConstraint("(state = 'PROCESSING' AND screenshot_id IS NULL AND lease_expires_at IS NOT NULL) OR (state = 'FAILED' AND screenshot_id IS NULL AND lease_expires_at IS NULL) OR (state = 'COMPLETED' AND screenshot_id = candidate_screenshot_id AND lease_expires_at IS NULL AND last_error_code IS NULL)", name="ck_upload_receipt_state_shape"),
        CheckConstraint("last_error_code IS NULL OR last_error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'", name="ck_upload_receipt_error_code"),
        Index("ix_upload_receipts_processing_lease_expires_at", "lease_expires_at", postgresql_where=text("state = 'PROCESSING'")),
        Index("ix_upload_receipts_project_id", "project_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PGUUID,
        ForeignKey(
            "projects.id",
            ondelete="RESTRICT",
            name="fk_upload_receipts_project",
        ),
    )
    client_upload_id: Mapped[UUID] = mapped_column(PGUUID)
    fingerprint_version: Mapped[int] = mapped_column(Integer)
    upload_protocol_version: Mapped[int] = mapped_column(Integer)
    request_fingerprint: Mapped[str] = mapped_column(CHAR(64))
    canonical_request: Mapped[bytes] = mapped_column(LargeBinary)
    state: Mapped[str] = mapped_column(String(16))
    attempt_generation: Mapped[int] = mapped_column(BigInteger)
    attempt_token: Mapped[UUID] = mapped_column(PGUUID)
    candidate_screenshot_id: Mapped[UUID] = mapped_column(PGUUID)
    candidate_storage_key: Mapped[str] = mapped_column(Text)
    screenshot_id: Mapped[UUID | None] = mapped_column(PGUUID)
    lease_expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.clock_timestamp())
