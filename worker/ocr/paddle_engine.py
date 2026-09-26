from __future__ import annotations

import hashlib
import importlib.metadata
import io
import os
import platform
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .errors import AdapterError
from .geometry import canonicalize_regions
from .schemas import validate_schema_instance


_MODEL_ROOT_ENV = "QA_OCR_MODEL_ROOT"
_REQUIRED_OPTIONS = frozenset(
    {
        "platform_system",
        "text_detection_model_name",
        "text_recognition_model_name",
        "text_det_limit_side_len",
        "text_det_limit_type",
        "text_det_thresh",
        "text_det_box_thresh",
        "text_det_unclip_ratio",
        "text_rec_score_thresh",
        "text_recognition_batch_size",
        "return_word_box",
        "use_doc_orientation_classify",
        "use_doc_unwarping",
        "use_textline_orientation",
        "engine",
        "enable_mkldnn",
        "enable_cinn",
        "pixel_format",
        "pixel_hash",
    }
)
_EXPECTED_FIXED_OPTIONS = {
    "text_det_limit_type": "max",
    "text_recognition_batch_size": 1,
    "return_word_box": False,
    "use_doc_orientation_classify": False,
    "use_doc_unwarping": False,
    "use_textline_orientation": False,
    "engine": "paddle_static",
    "enable_mkldnn": False,
    "enable_cinn": False,
    "pixel_format": "RGB8",
    "pixel_hash": "sha256-rgb8-row-major-v1",
}


def _jcs_sha256(value: object) -> str:
    try:
        import rfc8785
    except ImportError as error:
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _options(profile_manifest: Mapping[str, Any]) -> dict[str, object]:
    raw = profile_manifest.get("engine_options")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    options: dict[str, object] = {}
    for item in raw:
        if not isinstance(item, Mapping) or set(item) != {"name", "value"}:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        name = item["name"]
        if not isinstance(name, str) or name in options:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        options[name] = item["value"]
    if set(options) != _REQUIRED_OPTIONS:
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    for name, expected in _EXPECTED_FIXED_OPTIONS.items():
        if options[name] != expected:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    for name, minimum, maximum in (
        ("text_det_limit_side_len", 64, 4_000),
        ("text_det_thresh", 0, 1),
        ("text_det_box_thresh", 0, 1),
        ("text_det_unclip_ratio", 0, 10),
        ("text_rec_score_thresh", 0, 1),
    ):
        value = options[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not minimum <= value <= maximum
        ):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    return options


def _validate_locale(
    profile_manifest: Mapping[str, Any], source_facts: Mapping[str, Any]
) -> None:
    language_map = profile_manifest.get("language_map")
    if not isinstance(language_map, Mapping):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    aliases = language_map.get("aliases")
    if not isinstance(aliases, Sequence):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    normalized_locale = source_facts["locale_code"].replace("_", "-").casefold()
    families = [
        item.get("family")
        for item in aliases
        if isinstance(item, Mapping)
        and isinstance(item.get("input"), str)
        and item["input"].replace("_", "-").casefold() == normalized_locale
    ]
    if families != [source_facts["ocr_language"]]:
        raise AdapterError("MODEL_UNAVAILABLE", "OCR")


def _verify_packages(profile_manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    engine = profile_manifest.get("engine")
    if not isinstance(engine, Mapping):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    packages = engine.get("packages")
    if not isinstance(packages, Sequence):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    verified: list[dict[str, object]] = []
    for package in packages:
        if not isinstance(package, Mapping) or set(package) != {
            "name",
            "version",
            "filename",
            "byte_size",
            "sha256",
        }:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        name = package["name"]
        version = package["version"]
        sha256 = package["sha256"]
        if not all(isinstance(value, str) and value for value in (name, version, sha256)):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        try:
            actual_version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
        if actual_version != version:
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
        filename = package["filename"]
        byte_size = package["byte_size"]
        if (
            not isinstance(filename, str)
            or not filename.endswith(".whl")
            or isinstance(byte_size, bool)
            or not isinstance(byte_size, int)
            or byte_size <= 0
        ):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        verified.append(dict(package))
    opencv = [
        distribution.metadata["Name"]
        for distribution in importlib.metadata.distributions()
        if distribution.metadata["Name"].casefold().startswith("opencv")
    ]
    if opencv != ["opencv-contrib-python"]:
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
    return verified


def _verify_native_packages(profile_manifest: Mapping[str, Any]) -> list[dict[str, object]]:
    engine = profile_manifest.get("engine")
    if not isinstance(engine, Mapping):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    packages = engine.get("native_packages")
    if not isinstance(packages, Sequence) or isinstance(packages, (str, bytes, bytearray)):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    if platform.system() == "Windows":
        if packages:
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
        return []
    if platform.system() != "Linux" or not packages:
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
    verified: list[dict[str, object]] = []
    for package in packages:
        if not isinstance(package, Mapping) or set(package) != {
            "name",
            "version",
            "architecture",
            "copyright_sha256",
        }:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        if not all(isinstance(package[key], str) and package[key] for key in package):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        name = package["name"]
        try:
            completed = subprocess.run(
                ["dpkg-query", "-W", "-f=${Version}\\t${Architecture}", name],
                check=True,
                text=True,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            actual_version, actual_architecture = completed.stdout.split("\t")
            doc_name = name.split(":", 1)[0]
            copyright_bytes = (Path("/usr/share/doc") / doc_name / "copyright").read_bytes()
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
        if (
            actual_version != package["version"]
            or actual_architecture != package["architecture"]
            or hashlib.sha256(copyright_bytes).hexdigest() != package["copyright_sha256"]
        ):
            raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
        verified.append(dict(package))
    return verified


def _verify_models(
    profile_manifest: Mapping[str, Any], model_root: Path
) -> list[dict[str, object]]:
    models = profile_manifest.get("models")
    artifacts = profile_manifest.get("artifacts")
    if (
        not isinstance(models, Sequence)
        or isinstance(models, (str, bytes, bytearray))
        or len(models) != 2
        or not isinstance(artifacts, Sequence)
    ):
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    model_names = set(models)
    verified: list[dict[str, object]] = []
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        name = artifact.get("name")
        sha256 = artifact.get("sha256")
        byte_size = artifact.get("byte_size")
        if (
            not isinstance(name, str)
            or not isinstance(sha256, str)
            or isinstance(byte_size, bool)
            or not isinstance(byte_size, int)
            or byte_size <= 0
        ):
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] not in model_names:
            raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
        path = model_root / relative
        try:
            data = path.read_bytes()
        except OSError as error:
            raise AdapterError("MODEL_UNAVAILABLE", "OCR") from error
        if len(data) != byte_size or hashlib.sha256(data).hexdigest() != sha256:
            raise AdapterError("MODEL_UNAVAILABLE", "OCR")
        verified.append(
            {
                "name": name,
                "revision": artifact.get("revision"),
                "kind": artifact.get("kind"),
                "byte_size": byte_size,
                "sha256": sha256,
                "license_identifier": artifact.get("license_identifier"),
            }
        )
    if len(verified) != 6:
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    return verified


def _decode(source_bytes: bytes, width: int, height: int):
    try:
        import numpy as np
        from PIL import Image, UnidentifiedImageError

        with Image.open(io.BytesIO(source_bytes)) as source:
            if source.width != width or source.height != height:
                raise AdapterError("INPUT_HASH_MISMATCH", "OCR")
            raw_orientation = source.getexif().get(274)
            exif_orientation = (
                raw_orientation
                if isinstance(raw_orientation, int) and 1 <= raw_orientation <= 8
                else None
            )
            rgb = np.asarray(source.convert("RGB"), dtype=np.uint8).copy()
    except AdapterError:
        raise
    except (OSError, ValueError, UnidentifiedImageError) as error:
        raise AdapterError("SOURCE_DECODE_ERROR", "OCR") from error
    pixel_sha256 = hashlib.sha256(rgb.tobytes(order="C")).hexdigest()
    return rgb, exif_orientation, pixel_sha256


def execute_paddle(
    *,
    source_bytes: bytes,
    source_facts: Mapping[str, Any],
    profile_manifest: Mapping[str, Any],
    profile_sha256: str,
) -> dict[str, object]:
    started = time.perf_counter()
    options = _options(profile_manifest)
    if options["platform_system"] != platform.system():
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR")
    _validate_locale(profile_manifest, source_facts)
    packages = _verify_packages(profile_manifest)
    native_packages = _verify_native_packages(profile_manifest)
    model_root_value = os.environ.get(_MODEL_ROOT_ENV)
    if not model_root_value:
        raise AdapterError("MODEL_UNAVAILABLE", "OCR")
    model_root = Path(model_root_value).resolve()
    artifacts = _verify_models(profile_manifest, model_root)
    runtime_policy = profile_manifest.get("runtime_policy")
    if not isinstance(runtime_policy, Mapping) or dict(runtime_policy) != {
        "python": "3.12",
        "device": "cpu",
        "numeric_mode": "fp32",
        "thread_count": 1,
        "network_allowed": False,
    }:
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

    decode_started = time.perf_counter()
    rgb, exif_orientation, pixel_sha256 = _decode(
        source_bytes, source_facts["width"], source_facts["height"]
    )
    decode_finished = time.perf_counter()
    try:
        import cv2
        import paddle
        from paddleocr import PaddleOCR
    except ImportError as error:
        raise AdapterError("ENGINE_UNAVAILABLE", "OCR") from error
    paddle.set_device("cpu")
    paddle.set_flags({"FLAGS_paddle_num_threads": 1})
    detector = str(options["text_detection_model_name"])
    recognizer = str(options["text_recognition_model_name"])
    if set(profile_manifest["models"]) != {detector, recognizer}:
        raise AdapterError("PROFILE_DIGEST_MISMATCH", "OCR")
    inference_started = time.perf_counter()
    engine = None
    try:
        engine = PaddleOCR(
            text_detection_model_name=detector,
            text_detection_model_dir=str(model_root / detector),
            text_recognition_model_name=recognizer,
            text_recognition_model_dir=str(model_root / recognizer),
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_recognition_batch_size=1,
            text_det_limit_side_len=int(options["text_det_limit_side_len"]),
            text_det_limit_type="max",
            text_det_thresh=float(options["text_det_thresh"]),
            text_det_box_thresh=float(options["text_det_box_thresh"]),
            text_det_unclip_ratio=float(options["text_det_unclip_ratio"]),
            text_rec_score_thresh=float(options["text_rec_score_thresh"]),
            return_word_box=False,
            device="cpu",
            engine="paddle_static",
            precision="fp32",
            enable_mkldnn=False,
            cpu_threads=1,
            enable_cinn=False,
        )
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        engine_results = engine.predict(bgr)
    except Exception as error:
        raise AdapterError("ENGINE_INTERNAL_ERROR", "OCR") from error
    finally:
        if engine is not None:
            engine.close()
    inference_finished = time.perf_counter()
    if len(engine_results) != 1:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    result = engine_results[0]
    try:
        texts = list(result["rec_texts"])
        scores = list(result["rec_scores"])
        polygons = list(result["rec_polys"])
    except (KeyError, TypeError) as error:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR") from error
    if not len(texts) == len(scores) == len(polygons):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    raw_regions = [
        {
            "engine_region_index": index,
            "text": text,
            "confidence": score,
            "detection_confidence": None,
            "polygon": polygon.tolist() if hasattr(polygon, "tolist") else polygon,
        }
        for index, (text, score, polygon) in enumerate(zip(texts, scores, polygons))
    ]
    projection_started = time.perf_counter()
    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    regions, audit_regions = canonicalize_regions(
        raw_regions,
        width=source_facts["width"],
        height=source_facts["height"],
        original_to_inference_matrix3x3=identity,
    )
    projection_finished = time.perf_counter()
    runtime_manifest: dict[str, object] = {
        "profile_id": profile_manifest["profile_id"],
        "engine_name": "paddleocr",
        "engine_version": "3.7.0",
        "packages": packages,
        "native_packages": native_packages,
        "artifacts": artifacts,
        "locale_code": source_facts["locale_code"],
        "ocr_language": source_facts["ocr_language"],
        "detected_language": None,
        "detected_language_reason": "NOT_PROVIDED",
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "unicode_version": profile_manifest["unicode_version"],
        "rapidfuzz_version": profile_manifest["rapidfuzz_version"],
        "device": "cpu",
        "thread_count": 1,
        "numeric_mode": "fp32",
        "engine_options": profile_manifest["engine_options"],
        "determinism_limitations": [
            "CPU kernels may differ across instruction sets; packages, models, options, and decision thresholds are pinned."
        ],
    }
    runtime_manifest["runtime_manifest_sha256"] = _jcs_sha256(runtime_manifest)
    output: dict[str, object] = {
        "adapter_version": 1,
        "source_sha256": source_facts["source_sha256"],
        "profile_sha256": profile_sha256,
        "pixel_sha256": pixel_sha256,
        "runtime_manifest": runtime_manifest,
        "preprocessing": {
            "exif_policy": "ignored-v1",
            "exif_orientation": exif_orientation,
            "pixel_sha256": pixel_sha256,
            "steps": [
                {
                    "kind": "decode-rgb8-identity",
                    "input_width": source_facts["width"],
                    "input_height": source_facts["height"],
                    "output_width": source_facts["width"],
                    "output_height": source_facts["height"],
                    "matrix3x3": identity,
                }
            ],
            "original_to_inference_matrix3x3": identity,
        },
        "regions": regions,
        "raw_audit": {
            "schema_version": 1,
            "regions": audit_regions,
            "raw_output_sha256": _jcs_sha256({"regions": raw_regions}),
        },
        "timings_ms": {
            "decode": (decode_finished - decode_started) * 1_000,
            "inference": (inference_finished - inference_started) * 1_000,
            "projection": (projection_finished - projection_started) * 1_000,
            "total": (projection_finished - started) * 1_000,
        },
    }
    validate_schema_instance("ocr-adapter-output", output, stage="OCR")
    return output
