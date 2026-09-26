"""Bounded image inspection without re-encoding originals."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, UnidentifiedImageError

from .durable_fs import ensure_regular_file


MAX_IMAGE_BYTES = 20_971_520
MAX_DIMENSION = 16_384
MAX_PIXELS = 40_000_000


class ImageValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ImageFacts:
    file_hash: str
    size_bytes: int
    media_type: str
    extension: str
    width: int
    height: int


def inspect_image_bytes(data: bytes, expected_media_type: str | None = None) -> ImageFacts:
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_IMAGE_BYTES:
        raise ImageValidationError("image size is outside the accepted range")
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                kind = image.format
                width, height = image.size
                frames = getattr(image, "n_frames", 1)
                if kind not in {"PNG", "JPEG"}:
                    raise ImageValidationError("only PNG and JPEG are supported")
                media_type = "image/png" if kind == "PNG" else "image/jpeg"
                if expected_media_type is not None and expected_media_type != media_type:
                    raise ImageValidationError("declared MIME does not match image signature")
                if width <= 0 or height <= 0 or max(width, height) > MAX_DIMENSION:
                    raise ImageValidationError("image dimensions are outside the accepted range")
                if width * height > MAX_PIXELS or frames != 1:
                    raise ImageValidationError("image is oversized or animated")
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
    except ImageValidationError:
        raise
    except (
        OSError,
        ValueError,
        SyntaxError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ImageValidationError("image is invalid, truncated, animated, or oversized") from exc
    return ImageFacts(
        file_hash=sha256(data).hexdigest(),
        size_bytes=len(data),
        media_type=media_type,
        extension="png" if kind == "PNG" else "jpg",
        width=width,
        height=height,
    )


def inspect_image_file(path: str | Path, expected_media_type: str | None = None) -> ImageFacts:
    file_path = Path(path)
    result = ensure_regular_file(file_path)
    assert result is not None
    if not 1 <= result.st_size <= MAX_IMAGE_BYTES:
        raise ImageValidationError("image size is outside the accepted range")
    data = file_path.read_bytes()
    if len(data) != result.st_size:
        raise ImageValidationError("image changed while being read")
    return inspect_image_bytes(data, expected_media_type)
