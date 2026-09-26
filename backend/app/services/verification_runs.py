"""Public verification-run creation and immutable read services."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

import rfc8785
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from backend.app.errors import DomainError, not_found
from backend.app.models import (
    Build,
    Category,
    Locale,
    OCRProfile,
    OCRRegion,
    OCRResult,
    Project,
    Screenshot,
    Situation,
    SituationExpectedString,
    StringEntry,
    StringKey,
    VerificationExpectedItem,
    VerificationItem,
    VerificationJob,
    VerificationResult,
    VerificationRun,
)
from backend.app.workers.ocr_admission import AdmissionSnapshot, load_admission_snapshot
from worker.ocr import AdapterError
from worker.ocr.schemas import validate_schema_instance


MAX_SNAPSHOT_ITEMS = 1000
MAX_CANONICAL_BYTES = 8 * 1024 * 1024
RETRYABLE_SQLSTATES = {"40001", "40P01"}


@dataclass(frozen=True)
class CreateOutcome:
    run: dict
    replayed: bool


@dataclass
class _AdmissionEvaluation:
    loaded: bool = False
    snapshot: AdmissionSnapshot | None = None

    def get(self):
        if not self.loaded:
            self.snapshot = load_admission_snapshot()
            self.loaded = True
        return self.snapshot


def _sqlstate(exc):
    return getattr(getattr(exc, "orig", None), "sqlstate", None)


def _begin_creation(session):
    session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
    session.execute(text("SET LOCAL lock_timeout = '5s'"))
    session.execute(text("SET LOCAL statement_timeout = '10s'"))
    session.execute(text("SET LOCAL idle_in_transaction_session_timeout = '10s'"))
    if session.scalar(text("SELECT pg_is_in_recovery()")):
        raise DomainError(503, "DATABASE_UNAVAILABLE", "Database unavailable", retry_after=5)


def _decimal_json(value: Decimal):
    return int(value) if value == value.to_integral_value() else float(value)


def _canonical(payload, *, limit=MAX_CANONICAL_BYTES):
    try:
        value = rfc8785.dumps(payload)
    except (rfc8785.CanonicalizationError, TypeError, ValueError):
        raise DomainError(field="body", reason="value cannot be represented canonically") from None
    if not 1 <= len(value) <= limit:
        raise DomainError(422, "SNAPSHOT_LIMIT_EXCEEDED", "Snapshot exceeds configured limits")
    return value, hashlib.sha256(value).hexdigest()


def _profile_documents():
    try:
        from worker.ocr.profiles import iter_profile_documents
    except (ImportError, ModuleNotFoundError):
        return {}
    try:
        documents = list(iter_profile_documents())
        by_id = {document.profile_id: document for document in documents}
        if len(by_id) != len(documents):
            return {}
        return by_id
    except Exception:
        return {}


def _manifest(document):
    canonical = bytes(document.canonical_bytes)
    digest = hashlib.sha256(canonical).hexdigest()
    if digest != document.sha256 or not canonical or len(canonical) > MAX_CANONICAL_BYTES:
        raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5)
    try:
        manifest = json.loads(canonical)
        declared = dict(document.manifest)
        if (not isinstance(manifest, dict)
                or manifest.get("profile_id") != document.profile_id
                or rfc8785.dumps(manifest) != canonical
                or rfc8785.dumps(declared) != canonical):
            raise ValueError
        validate_schema_instance("profile-manifest", manifest, stage="OCR")
    except (
        AdapterError,
        AttributeError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        rfc8785.CanonicalizationError,
    ):
        raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5) from None
    return manifest, canonical, digest


def _profile_value(manifest, key, default=None):
    if key in manifest:
        return manifest[key]
    runtime = manifest.get("runtime")
    if isinstance(runtime, dict) and key in runtime:
        return runtime[key]
    engine = manifest.get("engine")
    if isinstance(engine, dict) and key in {"engine_name", "engine_version"}:
        return engine.get("name" if key == "engine_name" else "version", default)
    if key == "model_ids" and isinstance(manifest.get("models"), list):
        values = []
        for model in manifest["models"]:
            if isinstance(model, str) and model:
                values.append(model)
            elif isinstance(model, dict):
                value = model.get("model_id", model.get("name"))
                if isinstance(value, str) and value:
                    values.append(value)
        return values
    if key == "language_tags":
        language_map = manifest.get("language_map")
        aliases = language_map.get("aliases") if isinstance(language_map, dict) else None
        if isinstance(aliases, list):
            return sorted({alias["input"] for alias in aliases
                           if isinstance(alias, dict) and isinstance(alias.get("input"), str)})
    return default


def _profile_available(document, manifest, digest, admission):
    qualification = manifest.get("qualification")
    return (manifest.get("production_eligible") is True
            and isinstance(qualification, dict)
            and qualification.get("status") == "QUALIFIED"
            and getattr(document, "production_eligible", None) is True
            and admission is not None
            and admission.admitted(document.profile_id, digest))


def _profile_summary(profile, document=None, admission=None):
    manifest = None
    digest = profile.profile_digest
    if document is not None:
        try:
            manifest, _, digest = _manifest(document)
            if digest != profile.profile_digest:
                document = None
                manifest = None
        except DomainError:
            document = None
            manifest = None
    available = (
        manifest is not None
        and _profile_available(document, manifest, digest, admission)
    )
    return {
        "profile_id": profile.profile_id,
        "profile_digest": profile.profile_digest,
        "engine_name": profile.engine_name,
        "engine_version": profile.engine_version,
        "model_ids": profile.model_ids,
        "language_tags": profile.language_tags,
        "coordinate_space": profile.coordinate_space,
        "normalization_version": profile.normalization_version,
        "matching_version": profile.matching_version,
        "availability": "AVAILABLE" if available else "UNAVAILABLE",
        "unavailable_code": None if available else "UNQUALIFIED_RUNTIME",
    }


def _locale_language(manifest, locale_code):
    language_map = manifest.get("language_map")
    aliases = language_map.get("aliases") if isinstance(language_map, dict) else None
    if not isinstance(aliases, list):
        raise DomainError(422, "OCR_LOCALE_UNSUPPORTED", "Screenshot locale is unsupported")
    lookup = locale_code.replace("_", "-").lower()
    for alias in aliases:
        if not isinstance(alias, dict):
            continue
        source, family = alias.get("input"), alias.get("family")
        if (isinstance(source, str) and source.replace("_", "-").lower() == lookup
                and isinstance(family, str) and family):
            return family
    raise DomainError(422, "OCR_LOCALE_UNSUPPORTED", "Screenshot locale is unsupported")


def _request_payload(project_id, screenshot_id, body):
    thresholds = body.verification
    return {
        "protocol_version": 1,
        "project_id": str(project_id),
        "screenshot_id": str(screenshot_id),
        "profile_id": body.profile_id,
        "verification": {
            "pass_threshold": _decimal_json(thresholds.pass_threshold),
            "review_threshold": _decimal_json(thresholds.review_threshold),
        },
    }


def _error(row):
    if row.error_code is None:
        return None
    return {
        "code": row.error_code,
        "correlation_id": row.error_correlation_id,
        "cause_code": row.error_cause_code,
        "stage": row.error_stage,
        "retryable": row.error_retryable,
        "message": row.error_message,
        "attempt": row.error_attempt,
    }


def _summary(row):
    return {
        "id": row.id,
        "project_id": row.project_id,
        "screenshot_id": row.screenshot_id,
        "client_run_id": row.client_run_id,
        "protocol_version": row.protocol_version,
        "profile_id": row.profile_id,
        "profile_digest": row.profile_digest,
        "status": row.status,
        "stage": row.stage,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "attempt_count": row.attempt_count,
        "next_attempt_at": row.next_attempt_at,
        "verification_status": row.verification_status,
        "error": _error(row),
    }


def _serialize_run(row):
    result = _summary(row)
    base = f"/api/v1/projects/{row.project_id}/screenshots/{row.screenshot_id}/verification-runs/{row.id}"
    result.update({
        "snapshot": {
            "version": row.snapshot_version,
            "sha256": row.snapshot_sha256,
            "captured_at": row.captured_at,
            "item_count": row.snapshot_item_count,
            "missing_count": row.snapshot_missing_count,
            "locale_code": row.locale_code,
            "ocr_language": row.ocr_language,
            "screenshot_file_hash": row.screenshot_file_hash,
            "width": row.screenshot_width,
            "height": row.screenshot_height,
        },
        "configuration": {
            "profile_id": row.profile_id,
            "profile_digest": row.profile_digest,
            "normalization_version": row.normalization_version,
            "matching_version": row.matching_version,
            "pass_threshold": row.pass_threshold,
            "review_threshold": row.review_threshold,
        },
        "ocr_result_id": row.ocr_result_id,
        "verification_result_id": row.verification_result_id,
        "links": {
            "self": base,
            "expected": base + "/expected",
            "ocr": base + "/ocr",
            "regions": base + "/ocr/regions",
            "verification": base + "/verification",
            "items": base + "/verification/items",
        },
    })
    return result


def _scoped_screenshot(session, project_id, screenshot_id):
    row = session.execute(
        select(Screenshot, Build, Locale, Category, Situation)
        .join(Build, (Build.project_id == Screenshot.project_id) & (Build.id == Screenshot.build_id))
        .join(Locale, (Locale.project_id == Screenshot.project_id) & (Locale.id == Screenshot.locale_id))
        .join(Category, (Category.project_id == Screenshot.project_id) & (Category.id == Screenshot.category_id))
        .join(Situation, (Situation.project_id == Screenshot.project_id) & (Situation.id == Screenshot.situation_id))
        .where(Screenshot.project_id == project_id, Screenshot.id == screenshot_id)
    ).one_or_none()
    if row is None:
        raise not_found()
    return row


def _expected(session, screenshot):
    rows = session.execute(
        select(SituationExpectedString, StringKey, StringEntry)
        .join(StringKey, (StringKey.project_id == SituationExpectedString.project_id)
              & (StringKey.id == SituationExpectedString.string_key_id))
        .outerjoin(StringEntry, (StringEntry.project_id == SituationExpectedString.project_id)
                   & (StringEntry.build_id == SituationExpectedString.build_id)
                   & (StringEntry.locale_id == screenshot.locale_id)
                   & (StringEntry.string_key_id == SituationExpectedString.string_key_id))
        .where(
            SituationExpectedString.project_id == screenshot.project_id,
            SituationExpectedString.build_id == screenshot.build_id,
            SituationExpectedString.situation_id == screenshot.situation_id,
        )
        .order_by(SituationExpectedString.position)
    ).all()
    if len(rows) > MAX_SNAPSHOT_ITEMS:
        raise DomainError(422, "SNAPSHOT_LIMIT_EXCEEDED", "Snapshot exceeds configured limits")
    return [
        {
            "position": mapping.position,
            "string_key_id": key.id,
            "string_id": key.string_id,
            "entry_id": entry.id if entry else None,
            "expected_text": entry.text if entry else None,
            "translation_status": "present" if entry else "missing",
        }
        for mapping, key, entry in rows
    ]


def _existing(session, project_id, client_run_id):
    return session.scalar(select(VerificationRun).where(
        VerificationRun.project_id == project_id,
        VerificationRun.client_run_id == client_run_id,
    ))


def _compare_existing(row, fingerprint):
    if row.request_fingerprint != fingerprint:
        raise DomainError(409, "RUN_IDEMPOTENCY_CONFLICT", "Run identity conflicts")
    return CreateOutcome(_serialize_run(row), True)


def _insert_profile(session, document, manifest, canonical, digest):
    profile = session.get(OCRProfile, document.profile_id)
    if profile is not None:
        if profile.profile_digest != digest or profile.canonical_manifest != canonical:
            raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5)
        return profile
    required = {
        "engine_name": _profile_value(manifest, "engine_name"),
        "engine_version": _profile_value(manifest, "engine_version"),
        "model_ids": _profile_value(manifest, "model_ids"),
        "language_tags": _profile_value(manifest, "language_tags"),
        "coordinate_space": _profile_value(manifest, "coordinate_space"),
        "normalization_version": _profile_value(manifest, "normalization_version"),
        "matching_version": _profile_value(manifest, "matching_version"),
    }
    if any(value is None for value in required.values()):
        raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5)
    profile = OCRProfile(
        profile_id=document.profile_id,
        profile_digest=digest,
        canonical_manifest=canonical,
        **required,
    )
    session.add(profile)
    session.flush()
    return profile


def _create_once(session, project_id, screenshot_id, body, admission_evaluation):
    _begin_creation(session)
    screenshot, build, locale, category, situation = _scoped_screenshot(session, project_id, screenshot_id)
    request_canonical, fingerprint = _canonical(_request_payload(project_id, screenshot_id, body), limit=65536)
    existing = _existing(session, project_id, body.client_run_id)
    if existing is not None:
        return _compare_existing(existing, fingerprint)

    document = _profile_documents().get(body.profile_id)
    if document is None:
        if session.get(OCRProfile, body.profile_id) is not None:
            raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5)
        raise DomainError(422, "OCR_PROFILE_UNKNOWN", "OCR profile is unknown")
    manifest, profile_canonical, profile_digest = _manifest(document)
    admission = admission_evaluation.get()
    if not _profile_available(document, manifest, profile_digest, admission):
        raise DomainError(503, "OCR_PROFILE_UNAVAILABLE", "OCR profile unavailable", retry_after=5)
    ocr_language = _locale_language(manifest, locale.code)
    profile = _insert_profile(session, document, manifest, profile_canonical, profile_digest)
    expected = _expected(session, screenshot)
    captured_at = session.scalar(select(func.transaction_timestamp()))
    captured_text = captured_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
    snapshot_payload = {
        "snapshot_version": 1,
        "captured_at": captured_text,
        "source_mode": "run_creation",
        "screenshot": {
            "id": str(screenshot.id), "project_id": str(project_id),
            "storage_key": screenshot.storage_key, "file_hash": screenshot.file_hash,
            "size_bytes": screenshot.size_bytes, "media_type": screenshot.media_type,
            "width": screenshot.width, "height": screenshot.height,
            "build_id": str(screenshot.build_id), "locale_id": str(screenshot.locale_id),
            "category_id": str(screenshot.category_id), "situation_id": str(screenshot.situation_id),
            "metadata_version": screenshot.metadata_version, "metadata": screenshot.capture_metadata,
            "build_label": build.label, "locale_code": locale.code, "locale_name": locale.name,
            "category_slug": category.slug, "category_name": category.name,
            "situation_slug": situation.slug, "situation_name": situation.name,
            "situation_description": situation.description,
        },
        "ocr_language": ocr_language,
        "expected_items": [
            dict(item,
                 string_key_id=str(item["string_key_id"]),
                 entry_id=str(item["entry_id"]) if item["entry_id"] else None)
            for item in expected
        ],
        "item_count": len(expected),
        "missing_count": sum(item["translation_status"] == "missing" for item in expected),
    }
    snapshot_canonical, snapshot_sha256 = _canonical(snapshot_payload)
    config_payload = {
        "profile_id": profile.profile_id,
        "profile_digest": profile.profile_digest,
        "normalization_version": profile.normalization_version,
        "matching_version": profile.matching_version,
        "pass_threshold": _decimal_json(body.verification.pass_threshold),
        "review_threshold": _decimal_json(body.verification.review_threshold),
    }
    config_canonical, config_sha256 = _canonical(config_payload)
    now = session.scalar(select(func.clock_timestamp()))
    run = VerificationRun(
        id=uuid4(), project_id=project_id, screenshot_id=screenshot.id,
        client_run_id=body.client_run_id, protocol_version=1, fingerprint_version=1,
        request_fingerprint=fingerprint, canonical_request=request_canonical,
        profile_id=profile.profile_id, profile_digest=profile.profile_digest,
        profile_canonical=profile.canonical_manifest, snapshot_version=1,
        snapshot_canonical=snapshot_canonical, snapshot_sha256=snapshot_sha256,
        captured_at=captured_at, source_mode="run_creation",
        configuration_canonical=config_canonical, configuration_sha256=config_sha256,
        normalization_version=profile.normalization_version, matching_version=profile.matching_version,
        pass_threshold=body.verification.pass_threshold, review_threshold=body.verification.review_threshold,
        locale_code=locale.code, ocr_language=ocr_language,
        screenshot_storage_key=screenshot.storage_key, screenshot_file_hash=screenshot.file_hash,
        screenshot_size_bytes=screenshot.size_bytes, screenshot_media_type=screenshot.media_type,
        screenshot_width=screenshot.width, screenshot_height=screenshot.height,
        screenshot_build_id=screenshot.build_id, screenshot_locale_id=screenshot.locale_id,
        screenshot_category_id=screenshot.category_id, screenshot_situation_id=screenshot.situation_id,
        screenshot_metadata_version=screenshot.metadata_version, screenshot_metadata=screenshot.capture_metadata,
        build_label=build.label, locale_name=locale.name,
        category_slug=category.slug, category_name=category.name,
        situation_slug=situation.slug, situation_name=situation.name,
        situation_description=situation.description,
        snapshot_item_count=len(expected),
        snapshot_missing_count=sum(item["translation_status"] == "missing" for item in expected),
        status="PENDING", stage="QUEUED", attempt_count=0,
        next_attempt_at=None, verification_status=None,
        ocr_result_id=None, verification_result_id=None,
        error_code=None, error_correlation_id=None, error_cause_code=None,
        error_stage=None, error_retryable=None, error_message=None, error_attempt=None,
        created_at=now, updated_at=now, started_at=None, completed_at=None,
    )
    session.add(run)
    session.flush()
    for item in expected:
        session.add(VerificationExpectedItem(project_id=project_id, run_id=run.id, **item))
    session.add(VerificationJob(
        run_id=run.id, project_id=project_id, state="PENDING", stage="QUEUED",
        attempt_count=0, generation=0, attempt_token=None, lease_expires_at=None,
        available_at=now, next_attempt_at=None,
        last_error_code=None, last_error_correlation_id=None, last_error_cause_code=None,
        last_error_stage=None, last_error_retryable=None, last_error_message=None,
        last_error_attempt=None, created_at=now, updated_at=now,
        started_at=None, completed_at=None,
    ))
    session.flush()
    session.commit()
    return CreateOutcome(_serialize_run(run), False)


def _recover(factory, project_id, client_run_id, fingerprint):
    with factory() as recovery:
        _begin_creation(recovery)
        row = _existing(recovery, project_id, client_run_id)
        if row is None:
            return None
        return _compare_existing(row, fingerprint)


def create_or_replay(session, project_id, screenshot_id, body):
    factory = sessionmaker(session.get_bind(), expire_on_commit=False)
    _, fingerprint = _canonical(_request_payload(project_id, screenshot_id, body), limit=65536)
    admission_evaluation = _AdmissionEvaluation()
    for attempt in range(3):
        try:
            with factory() as current:
                return _create_once(
                    current,
                    project_id,
                    screenshot_id,
                    body,
                    admission_evaluation,
                )
        except IntegrityError as exc:
            if _sqlstate(exc) == "23505":
                recovered = _recover(factory, project_id, body.client_run_id, fingerprint)
                if recovered is not None:
                    return recovered
            raise
        except SQLAlchemyError as exc:
            if _sqlstate(exc) in RETRYABLE_SQLSTATES and attempt < 2:
                continue
            if _sqlstate(exc) not in RETRYABLE_SQLSTATES:
                recovered = _recover(factory, project_id, body.client_run_id, fingerprint)
                if recovered is not None:
                    return recovered
            raise DomainError(503, "DATABASE_UNAVAILABLE", "Database unavailable", retry_after=5) from None
    raise DomainError(503, "DATABASE_UNAVAILABLE", "Database unavailable", retry_after=5)


def _lookup_run(session, project_id, screenshot_id, run_id):
    row = session.scalar(select(VerificationRun).where(
        VerificationRun.project_id == project_id,
        VerificationRun.screenshot_id == screenshot_id,
        VerificationRun.id == run_id,
    ))
    if row is None:
        raise not_found()
    return row


def list_runs(session, project_id, screenshot_id, selection, limit, offset):
    _scoped_screenshot(session, project_id, screenshot_id)
    predicates = [VerificationRun.project_id == project_id, VerificationRun.screenshot_id == screenshot_id]
    if selection == "succeeded":
        predicates.append(VerificationRun.status == "SUCCEEDED")
    total = session.scalar(select(func.count()).select_from(VerificationRun).where(*predicates))
    rows = session.scalars(select(VerificationRun).where(*predicates).order_by(
        VerificationRun.created_at.desc(), VerificationRun.id.desc()).offset(offset).limit(limit)).all()
    return {"items": [_summary(row) for row in rows], "total": total, "limit": limit, "offset": offset}


def get_run(session, project_id, screenshot_id, run_id):
    return _serialize_run(_lookup_run(session, project_id, screenshot_id, run_id))


def list_expected(session, project_id, screenshot_id, run_id, limit, offset):
    _lookup_run(session, project_id, screenshot_id, run_id)
    predicates = [VerificationExpectedItem.project_id == project_id, VerificationExpectedItem.run_id == run_id]
    total = session.scalar(select(func.count()).select_from(VerificationExpectedItem).where(*predicates))
    rows = session.scalars(select(VerificationExpectedItem).where(*predicates).order_by(
        VerificationExpectedItem.position).offset(offset).limit(limit)).all()
    return {"items": [{
        "position": row.position, "string_key_id": row.string_key_id, "string_id": row.string_id,
        "entry_id": row.entry_id, "expected_text": row.expected_text,
        "translation_status": row.translation_status,
    } for row in rows], "total": total, "limit": limit, "offset": offset}


def _ready(row):
    if row.status != "SUCCEEDED":
        raise DomainError(409, "RESULT_NOT_READY", "Result is not ready")


def get_ocr(session, project_id, screenshot_id, run_id):
    run = _lookup_run(session, project_id, screenshot_id, run_id)
    _ready(run)
    row = session.scalar(select(OCRResult).where(OCRResult.project_id == project_id, OCRResult.run_id == run_id))
    if row is None:
        raise DomainError(409, "RESULT_NOT_READY", "Result is not ready")
    return {
        "id": row.id, "run_id": row.run_id, "project_id": row.project_id,
        "screenshot_id": row.screenshot_id, "coordinate_space": row.coordinate_space,
        "width": row.width, "height": row.height, "region_count": row.region_count,
        "no_text": row.no_text, "profile_id": row.profile_id,
        "profile_digest": row.profile_digest, "engine_name": row.engine_name,
        "engine_version": row.engine_version, "ocr_language": row.ocr_language,
        "runtime_manifest": row.runtime_manifest, "preprocessing": row.preprocessing,
        "output_sha256": row.output_sha256, "created_at": row.created_at,
    }


def list_regions(session, project_id, screenshot_id, run_id, limit, offset):
    run = _lookup_run(session, project_id, screenshot_id, run_id)
    _ready(run)
    predicates = [OCRRegion.project_id == project_id, OCRRegion.run_id == run_id]
    total = session.scalar(select(func.count()).select_from(OCRRegion).where(*predicates))
    rows = session.scalars(select(OCRRegion).where(*predicates).order_by(OCRRegion.region_index).offset(offset).limit(limit)).all()
    return {"items": [{
        "region_index": row.region_index, "text": row.raw_text, "confidence": row.confidence,
        "confidence_semantics": row.confidence_semantics,
        "detection_confidence": row.detection_confidence,
        "detection_confidence_unavailable_reason": row.detection_confidence_unavailable_reason,
        "polygon": row.polygon,
        "bbox": {"x": row.bbox_x, "y": row.bbox_y, "width": row.bbox_width, "height": row.bbox_height},
        "clipped": row.clipped, "engine_region_index": row.engine_region_index,
    } for row in rows], "total": total, "limit": limit, "offset": offset}


def get_verification(session, project_id, screenshot_id, run_id):
    run = _lookup_run(session, project_id, screenshot_id, run_id)
    _ready(run)
    row = session.scalar(select(VerificationResult).where(
        VerificationResult.project_id == project_id, VerificationResult.run_id == run_id))
    if row is None:
        raise DomainError(409, "RESULT_NOT_READY", "Result is not ready")
    return {column.key: getattr(row, column.key) for column in row.__mapper__.column_attrs}


def list_verification_items(session, project_id, screenshot_id, run_id, limit, offset):
    run = _lookup_run(session, project_id, screenshot_id, run_id)
    _ready(run)
    predicates = [VerificationItem.project_id == project_id, VerificationItem.run_id == run_id]
    total = session.scalar(select(func.count()).select_from(VerificationItem).where(*predicates))
    rows = session.scalars(select(VerificationItem).where(*predicates).order_by(
        VerificationItem.expected_position).offset(offset).limit(limit)).all()
    names = [column.key for column in VerificationItem.__mapper__.column_attrs
             if column.key not in {"project_id", "run_id", "verification_result_id", "ocr_result_id"}]
    return {"items": [{name: getattr(row, name) for name in names} for row in rows],
            "total": total, "limit": limit, "offset": offset}


def list_profiles(session, project_id):
    if session.get(Project, project_id) is None:
        raise not_found()
    documents = _profile_documents()
    admission = load_admission_snapshot()
    rows = {row.profile_id: row for row in session.scalars(select(OCRProfile)).all()}
    items = [
        _profile_summary(row, documents.get(profile_id), admission)
        for profile_id, row in rows.items()
    ]
    for profile_id, document in documents.items():
        if profile_id in rows:
            continue
        try:
            manifest, canonical, digest = _manifest(document)
            proxy = type("ProfileProxy", (), {
                "profile_id": profile_id, "profile_digest": digest,
                "engine_name": _profile_value(manifest, "engine_name", "unknown"),
                "engine_version": _profile_value(manifest, "engine_version", "unknown"),
                "model_ids": _profile_value(manifest, "model_ids", []),
                "language_tags": _profile_value(manifest, "language_tags", []),
                "coordinate_space": _profile_value(manifest, "coordinate_space", "original-raster-v1"),
                "normalization_version": _profile_value(manifest, "normalization_version", "norm-v1"),
                "matching_version": _profile_value(manifest, "matching_version", "one-to-one-levenshtein-v1"),
            })()
            items.append(_profile_summary(proxy, document, admission))
        except DomainError:
            continue
    return {"items": sorted(items, key=lambda item: item["profile_id"])}
