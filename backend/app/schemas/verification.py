from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, PlainSerializer, UUID4, field_validator, model_validator

from .common import Closed, StringId, Text


Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
JsonDecimal = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]
Threshold = Annotated[JsonDecimal, Field(ge=Decimal("0"), le=Decimal("100"))]
Score = Annotated[JsonDecimal, Field(ge=Decimal("0"), le=Decimal("100"))]
Confidence = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
Coordinate = Annotated[FiniteFloat, Field(ge=0)]
PositiveExtent = Annotated[FiniteFloat, Field(gt=0)]
ProfileId = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"),
]
RunStatus = Literal["PENDING", "RUNNING", "RETRY_WAIT", "SUCCEEDED", "FAILED"]
RunStage = Literal["QUEUED", "OCR", "VERIFY", "COMPLETE"]
QualityStatus = Literal["PASS", "REVIEW", "FAIL", "UNVERIFIED"]


def _exact_decimal(value: Any, field: str) -> Any:
    if isinstance(value, bool) or isinstance(value, str) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{field} must be a JSON number")
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError(f"{field} must be finite")
    if decimal.as_tuple().exponent < -2:
        raise ValueError(f"{field} must have at most 2 decimal places")
    return decimal


class VerificationThresholds(Closed):
    pass_threshold: Threshold = Decimal("95")
    review_threshold: Threshold = Decimal("85")

    @field_validator("pass_threshold", "review_threshold", mode="before")
    @classmethod
    def exact_threshold(cls, value: Any, info):
        return _exact_decimal(value, info.field_name)

    @model_validator(mode="after")
    def ordered_thresholds(self):
        if self.review_threshold >= self.pass_threshold:
            raise ValueError("review_threshold must be less than pass_threshold")
        return self


class VerificationRunCreate(Closed):
    protocol_version: Literal[1]
    client_run_id: UUID4
    profile_id: ProfileId
    verification: VerificationThresholds = Field(default_factory=VerificationThresholds)

    @field_validator("protocol_version", mode="before")
    @classmethod
    def integer_protocol_version(cls, value: Any):
        if type(value) is not int:
            raise ValueError("protocol_version must be integer 1")
        return value


class RunError(Closed):
    code: str
    correlation_id: UUID
    cause_code: str | None
    stage: Literal["QUEUED", "OCR", "VERIFY"]
    retryable: bool
    message: str
    attempt: int = Field(ge=1, le=3)


class VerificationRunSummary(Closed):
    id: UUID
    project_id: UUID
    screenshot_id: UUID
    client_run_id: UUID
    protocol_version: Literal[1]
    profile_id: ProfileId
    profile_digest: Sha256
    status: RunStatus
    stage: RunStage
    created_at: AwareDatetime
    updated_at: AwareDatetime
    started_at: AwareDatetime | None
    completed_at: AwareDatetime | None
    attempt_count: int = Field(ge=0, le=3)
    next_attempt_at: AwareDatetime | None
    verification_status: QualityStatus | None
    error: RunError | None


class RunSnapshot(Closed):
    version: Literal[1]
    sha256: Sha256
    captured_at: AwareDatetime
    item_count: int = Field(ge=0, le=1000)
    missing_count: int = Field(ge=0, le=1000)
    locale_code: str
    ocr_language: str
    screenshot_file_hash: Sha256
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class RunConfiguration(Closed):
    profile_id: ProfileId
    profile_digest: Sha256
    normalization_version: str
    matching_version: str
    pass_threshold: Threshold
    review_threshold: Threshold


class RunLinks(Closed):
    self: str
    expected: str
    ocr: str
    regions: str
    verification: str
    items: str


class VerificationRun(VerificationRunSummary):
    snapshot: RunSnapshot
    configuration: RunConfiguration
    ocr_result_id: UUID | None
    verification_result_id: UUID | None
    links: RunLinks


class ExpectedItem(Closed):
    position: int = Field(ge=0)
    string_key_id: UUID
    string_id: StringId
    entry_id: UUID | None
    expected_text: Text | None
    translation_status: Literal["present", "missing"]


class MatrixStep(Closed):
    kind: str
    input_width: int = Field(gt=0)
    input_height: int = Field(gt=0)
    output_width: int = Field(gt=0)
    output_height: int = Field(gt=0)
    matrix3x3: list[list[FiniteFloat]]

    @field_validator("matrix3x3")
    @classmethod
    def matrix_shape(cls, value):
        if len(value) != 3 or any(len(row) != 3 for row in value):
            raise ValueError("matrix3x3 must contain three rows of three numbers")
        return value


class Preprocessing(Closed):
    exif_policy: Literal["ignored-v1"]
    exif_orientation: int | None
    pixel_sha256: Sha256
    steps: list[MatrixStep]
    original_to_inference_matrix3x3: list[list[FiniteFloat]]

    @field_validator("original_to_inference_matrix3x3")
    @classmethod
    def matrix_shape(cls, value):
        if len(value) != 3 or any(len(row) != 3 for row in value):
            raise ValueError("matrix3x3 must contain three rows of three numbers")
        return value


class OcrSummary(Closed):
    id: UUID
    run_id: UUID
    project_id: UUID
    screenshot_id: UUID
    coordinate_space: Literal["original-raster-v1"]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    region_count: int = Field(ge=0, le=1000)
    no_text: bool
    profile_id: ProfileId
    profile_digest: Sha256
    engine_name: str
    engine_version: str
    ocr_language: str
    runtime_manifest: dict[str, Any]
    preprocessing: Preprocessing
    output_sha256: Sha256
    created_at: AwareDatetime


class BoundingBox(Closed):
    x: Coordinate
    y: Coordinate
    width: PositiveExtent
    height: PositiveExtent


class OcrRegion(Closed):
    region_index: int = Field(ge=0)
    text: Text
    confidence: Confidence
    confidence_semantics: Literal["recognition"]
    detection_confidence: Confidence | None
    detection_confidence_unavailable_reason: Literal["NOT_EXPOSED_BY_PROFILE"] | None
    polygon: list[list[FiniteFloat]] = Field(min_length=3, max_length=8)
    bbox: BoundingBox
    clipped: bool
    engine_region_index: int = Field(ge=0)

    @field_validator("polygon")
    @classmethod
    def polygon_points(cls, value):
        if any(len(point) != 2 for point in value):
            raise ValueError("polygon points must contain x and y")
        return value

    @model_validator(mode="after")
    def detection_confidence_pair(self):
        if (self.detection_confidence is None) != (
            self.detection_confidence_unavailable_reason == "NOT_EXPOSED_BY_PROFILE"
        ):
            raise ValueError("detection confidence and unavailable reason are inconsistent")
        return self


class VerificationSummary(Closed):
    id: UUID
    run_id: UUID
    project_id: UUID
    screenshot_id: UUID
    ocr_result_id: UUID
    snapshot_sha256: Sha256
    configuration_sha256: Sha256
    matching_version: str
    normalization_version: str
    verification_status: QualityStatus
    evaluation_reason: Literal["EVALUATED", "PARTIAL_UNVERIFIED", "NO_EVALUABLE_EXPECTATIONS", "NO_EXPECTATIONS"]
    incomplete: bool
    total_count: int = Field(ge=0)
    evaluated_count: int = Field(ge=0)
    unverified_count: int = Field(ge=0)
    pass_count: int = Field(ge=0)
    review_count: int = Field(ge=0)
    fail_count: int = Field(ge=0)
    unmatched_region_count: int = Field(ge=0)
    pass_threshold: Threshold
    review_threshold: Threshold
    created_at: AwareDatetime


class VerificationItem(Closed):
    expected_position: int = Field(ge=0)
    string_key_id: UUID
    string_id: StringId
    entry_id: UUID | None
    expected_text: Text | None
    normalized_expected: Text | None
    translation_status: Literal["present", "missing"]
    region_index: Annotated[int, Field(ge=0)] | None
    observed_text: Text | None
    normalized_observed: Text | None
    match_method: Literal["EXACT", "NORMALIZED", "FUZZY", "NONE"] | None
    match_score: Score | None
    score_numerator: Annotated[int, Field(ge=0)] | None
    score_denominator: Annotated[int, Field(ge=1)] | None
    verification_status: QualityStatus
    reason: Literal["MATCHED", "NO_MATCH", "MISSING_TRANSLATION", "EMPTY_EXPECTED", "NORMALIZED_EMPTY_EXPECTED"]


class ProfileSummary(Closed):
    profile_id: ProfileId
    profile_digest: Sha256
    engine_name: str
    engine_version: str
    model_ids: list[str]
    language_tags: list[str]
    coordinate_space: Literal["original-raster-v1"]
    normalization_version: str
    matching_version: str
    availability: Literal["AVAILABLE", "UNAVAILABLE"]
    unavailable_code: str | None


class ProfileList(Closed):
    items: list[ProfileSummary]
