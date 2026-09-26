from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from .errors import AdapterError
from .validation import (
    require_closed_mapping,
    require_finite_number,
    require_int,
    require_scalar_text,
    require_sequence,
)


Point = tuple[float, float]
Matrix3 = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


def _matrix3(value: object) -> Matrix3:
    rows = require_sequence(value, stage="OCR", code="ENGINE_OUTPUT_INVALID")
    if len(rows) != 3:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    parsed: list[tuple[float, float, float]] = []
    for row in rows:
        columns = require_sequence(row, stage="OCR", code="ENGINE_OUTPUT_INVALID")
        if len(columns) != 3:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        parsed.append(
            tuple(
                require_finite_number(
                    item,
                    stage="OCR",
                    code="ENGINE_OUTPUT_INVALID",
                )
                for item in columns
            )  # type: ignore[arg-type]
        )
    return (parsed[0], parsed[1], parsed[2])


def invert_matrix3(value: object) -> Matrix3:
    matrix = _matrix3(value)
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if not math.isfinite(determinant) or abs(determinant) <= 1e-15:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    inverse = (
        (
            (e * i - f * h) / determinant,
            (c * h - b * i) / determinant,
            (b * f - c * e) / determinant,
        ),
        (
            (f * g - d * i) / determinant,
            (a * i - c * g) / determinant,
            (c * d - a * f) / determinant,
        ),
        (
            (d * h - e * g) / determinant,
            (b * g - a * h) / determinant,
            (a * e - b * d) / determinant,
        ),
    )
    if not all(math.isfinite(item) for row in inverse for item in row):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    return inverse


def transform_point(matrix: Matrix3, point: Point) -> Point:
    x, y = point
    tx = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]
    ty = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]
    tw = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2]
    if not math.isfinite(tw) or abs(tw) <= 1e-15:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    result = (tx / tw, ty / tw)
    if not all(math.isfinite(value) for value in result):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    return result


def _signed_area(polygon: list[Point]) -> float:
    return 0.5 * sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1])
    )


def _clockwise_quad(points: list[Point]) -> list[Point]:
    if len(points) != 4 or len(set(points)) != 4:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    center_x = sum(point[0] for point in points) / 4
    center_y = sum(point[1] for point in points) / 4
    ordered = sorted(
        points,
        key=lambda point: math.atan2(point[1] - center_y, point[0] - center_x),
    )
    if _signed_area(ordered) < 0:
        ordered.reverse()
    if _signed_area(ordered) <= 1e-12:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    signs: list[float] = []
    for index in range(4):
        first = ordered[index]
        second = ordered[(index + 1) % 4]
        third = ordered[(index + 2) % 4]
        cross = (second[0] - first[0]) * (third[1] - second[1]) - (
            second[1] - first[1]
        ) * (third[0] - second[0])
        if abs(cross) <= 1e-12:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        signs.append(cross)
    if not (all(value > 0 for value in signs) or all(value < 0 for value in signs)):
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    start = min(range(4), key=lambda index: (ordered[index][1], ordered[index][0]))
    return ordered[start:] + ordered[:start]


def _clip_boundary(
    polygon: list[Point],
    *,
    inside: Any,
    intersection: Any,
) -> list[Point]:
    if not polygon:
        return []
    output: list[Point] = []
    previous = polygon[-1]
    previous_inside = inside(previous)
    for current in polygon:
        current_inside = inside(current)
        if current_inside:
            if not previous_inside:
                output.append(intersection(previous, current))
            output.append(current)
        elif previous_inside:
            output.append(intersection(previous, current))
        previous = current
        previous_inside = current_inside
    return output


def _intersect_vertical(first: Point, second: Point, x: float) -> Point:
    dx = second[0] - first[0]
    if abs(dx) <= 1e-15:
        return (x, first[1])
    ratio = (x - first[0]) / dx
    return (x, first[1] + ratio * (second[1] - first[1]))


def _intersect_horizontal(first: Point, second: Point, y: float) -> Point:
    dy = second[1] - first[1]
    if abs(dy) <= 1e-15:
        return (first[0], y)
    ratio = (y - first[1]) / dy
    return (first[0] + ratio * (second[0] - first[0]), y)


def clip_polygon(polygon: list[Point], width: int, height: int) -> list[Point]:
    result = polygon
    result = _clip_boundary(
        result,
        inside=lambda point: point[0] >= 0,
        intersection=lambda first, second: _intersect_vertical(first, second, 0.0),
    )
    result = _clip_boundary(
        result,
        inside=lambda point: point[0] <= width,
        intersection=lambda first, second: _intersect_vertical(
            first, second, float(width)
        ),
    )
    result = _clip_boundary(
        result,
        inside=lambda point: point[1] >= 0,
        intersection=lambda first, second: _intersect_horizontal(first, second, 0.0),
    )
    result = _clip_boundary(
        result,
        inside=lambda point: point[1] <= height,
        intersection=lambda first, second: _intersect_horizontal(
            first, second, float(height)
        ),
    )
    return result


def _round_six(value: float) -> float:
    rounded = Decimal(str(value)).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_EVEN,
    )
    if rounded == 0:
        return 0.0
    return float(rounded)


def _round_polygon(polygon: list[Point]) -> list[list[float]]:
    rounded: list[list[float]] = []
    for x, y in polygon:
        point = [_round_six(x), _round_six(y)]
        if not rounded or point != rounded[-1]:
            rounded.append(point)
    if len(rounded) > 1 and rounded[0] == rounded[-1]:
        rounded.pop()
    if not 3 <= len(rounded) <= 8:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    area = _signed_area([(point[0], point[1]) for point in rounded])
    if not math.isfinite(area) or area <= 0:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    start = min(range(len(rounded)), key=lambda index: (rounded[index][1], rounded[index][0]))
    return rounded[start:] + rounded[:start]


def _polygon_jcs_bytes(polygon: list[list[float]]) -> bytes:
    def number(value: float) -> str:
        text = format(Decimal(str(value)), "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text if text not in ("", "-0") else "0"

    return (
        "["
        + ",".join(
            f"[{number(point[0])},{number(point[1])}]" for point in polygon
        )
        + "]"
    ).encode("ascii")


def _parse_quad(value: object) -> list[Point]:
    raw_points = require_sequence(value, stage="OCR", code="ENGINE_OUTPUT_INVALID")
    if len(raw_points) != 4:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    points: list[Point] = []
    for raw_point in raw_points:
        coordinates = require_sequence(
            raw_point,
            stage="OCR",
            code="ENGINE_OUTPUT_INVALID",
        )
        if len(coordinates) != 2:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        points.append(
            (
                require_finite_number(
                    coordinates[0], stage="OCR", code="ENGINE_OUTPUT_INVALID"
                ),
                require_finite_number(
                    coordinates[1], stage="OCR", code="ENGINE_OUTPUT_INVALID"
                ),
            )
        )
    return points


def canonicalize_regions(
    raw_regions: object,
    *,
    width: int,
    height: int,
    original_to_inference_matrix3x3: object,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if isinstance(width, bool) or isinstance(height, bool) or width <= 0 or height <= 0:
        raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
    values = require_sequence(raw_regions, stage="OCR", code="ENGINE_OUTPUT_INVALID")
    if len(values) > 1_000:
        raise AdapterError("RESULT_LIMIT_EXCEEDED", "OCR")
    inverse = invert_matrix3(original_to_inference_matrix3x3)
    projected: list[tuple[dict[str, object], dict[str, object], bytes, int]] = []
    total_text_bytes = 0
    for ordinal, raw_value in enumerate(values):
        raw = require_closed_mapping(
            raw_value,
            required=frozenset(
                {
                    "engine_region_index",
                    "text",
                    "confidence",
                    "detection_confidence",
                    "polygon",
                }
            ),
            stage="OCR",
            code="ENGINE_OUTPUT_INVALID",
        )
        engine_index = require_int(
            raw["engine_region_index"],
            minimum=0,
            stage="OCR",
            code="ENGINE_OUTPUT_INVALID",
        )
        text = require_scalar_text(
            raw["text"],
            maximum=10_000,
            stage="OCR",
            code="ENGINE_OUTPUT_INVALID",
        )
        total_text_bytes += len(text.encode("utf-8"))
        if total_text_bytes > 1_048_576:
            raise AdapterError("RESULT_LIMIT_EXCEEDED", "OCR")
        confidence = require_finite_number(
            raw["confidence"],
            minimum=0,
            maximum=1,
            stage="OCR",
            code="ENGINE_OUTPUT_INVALID",
        )
        detection = raw["detection_confidence"]
        if detection is None:
            detection_reason = "NOT_EXPOSED_BY_PROFILE"
        else:
            detection = require_finite_number(
                detection,
                minimum=0,
                maximum=1,
                stage="OCR",
                code="ENGINE_OUTPUT_INVALID",
            )
            detection_reason = None
        engine_quad = _parse_quad(raw["polygon"])
        transformed = _clockwise_quad(
            [transform_point(inverse, point) for point in engine_quad]
        )
        clipped_unrounded = clip_polygon(transformed, width, height)
        if len(clipped_unrounded) < 3 or _signed_area(clipped_unrounded) <= 1e-12:
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        clipped = any(
            point[0] < 0 or point[0] > width or point[1] < 0 or point[1] > height
            for point in transformed
        )
        polygon = _round_polygon(clipped_unrounded)
        min_x = min(point[0] for point in clipped_unrounded)
        max_x = max(point[0] for point in clipped_unrounded)
        min_y = min(point[1] for point in clipped_unrounded)
        max_y = max(point[1] for point in clipped_unrounded)
        bbox = {
            "x": math.floor(min_x),
            "y": math.floor(min_y),
            "width": math.ceil(max_x) - math.floor(min_x),
            "height": math.ceil(max_y) - math.floor(min_y),
        }
        if not (
            0 <= bbox["x"] < width
            and 0 <= bbox["y"] < height
            and 0 < bbox["width"] <= width
            and 0 < bbox["height"] <= height
            and bbox["x"] + bbox["width"] <= width
            and bbox["y"] + bbox["height"] <= height
        ):
            raise AdapterError("ENGINE_OUTPUT_INVALID", "OCR")
        public = {
            "region_index": -1,
            "text": text,
            "confidence": confidence,
            "confidence_semantics": "recognition",
            "detection_confidence": detection,
            "detection_confidence_unavailable_reason": detection_reason,
            "polygon": polygon,
            "bbox": bbox,
            "clipped": clipped,
            "engine_region_index": engine_index,
        }
        audit = {
            "engine_region_index": engine_index,
            "raw_text": text,
            "engine_polygon": [[x, y] for x, y in engine_quad],
            "transformed_preclip_polygon": [[x, y] for x, y in transformed],
            "recognition_confidence": confidence,
            "detection_confidence": detection,
        }
        polygon_key = _polygon_jcs_bytes(polygon)
        projected.append((public, audit, polygon_key, ordinal))
    projected.sort(
        key=lambda item: (
            item[0]["bbox"]["y"],  # type: ignore[index]
            item[0]["bbox"]["x"],  # type: ignore[index]
            item[0]["bbox"]["height"],  # type: ignore[index]
            item[0]["bbox"]["width"],  # type: ignore[index]
            item[2],
            item[0]["text"].encode("utf-8"),  # type: ignore[union-attr]
            item[3],
        )
    )
    public_regions: list[dict[str, object]] = []
    audit_regions: list[dict[str, object]] = []
    for index, (public, audit, _, _) in enumerate(projected):
        public["region_index"] = index
        public_regions.append(public)
        audit_regions.append(audit)
    return public_regions, audit_regions
