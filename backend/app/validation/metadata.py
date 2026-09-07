import json
import math
from uuid import UUID
from backend.app.errors import DomainError
from .unicode import validate_unicode


def validate_metadata(value):
    path = "metadata.metadata"
    validate_unicode(value, path)
    def fail(reason):
        raise DomainError(field=path, reason=reason)
    if not isinstance(value, dict):
        fail("must be an object")
    keys = 0
    def walk(item, depth):
        nonlocal keys
        if isinstance(item, (dict, list)):
            if depth > 5:
                fail("maximum container depth is 5")
            if isinstance(item, dict):
                keys += len(item)
                if keys > 100:
                    fail("maximum object key count is 100")
            for child in item.values() if isinstance(item, dict) else item:
                walk(child, depth + 1)
        elif isinstance(item, float) and not math.isfinite(item):
            fail("nonfinite numbers are not allowed")
    walk(value, 1)
    if len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")) > 16384:
        fail("maximum metadata size is 16 KiB")
    for key, limit in (("device", 200), ("scenario", 128), ("checkpoint", 128), ("screen_state", 128)):
        if key in value and (not isinstance(value[key], str) or len(value[key]) > limit):
            fail(f"{key} must be a string of at most {limit} scalars")
    if "run_id" in value:
        try:
            if not isinstance(value["run_id"], str):
                fail("run_id must be a UUID string")
            UUID(value["run_id"])
        except (ValueError, TypeError):
            fail("run_id must be a UUID string")
    if "resolution" in value:
        resolution = value["resolution"]
        if not isinstance(resolution, dict) or set(resolution) != {"width", "height"} or any(type(v) is not int or not 1 <= v <= 16384 for v in resolution.values()):
            fail("resolution must have positive integer width and height <=16384")
    return value
