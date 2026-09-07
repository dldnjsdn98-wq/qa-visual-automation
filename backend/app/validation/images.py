import warnings
from dataclasses import dataclass
from PIL import Image, UnidentifiedImageError
from backend.app.errors import DomainError

Image.MAX_IMAGE_PIXELS = 40_000_000


@dataclass(frozen=True)
class ImageFacts:
    width: int
    height: int
    media_type: str
    extension: str


def inspect_image(stream, media_type):
    if media_type not in ("image/png", "image/jpeg"):
        raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "Only PNG and JPEG are supported")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            stream.seek(0)
            with Image.open(stream) as image:
                kind = image.format
                width, height = image.size
                if kind not in ("PNG", "JPEG"):
                    raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "Only PNG and JPEG are supported")
                actual = "image/png" if kind == "PNG" else "image/jpeg"
                if actual != media_type:
                    raise DomainError(415, "UNSUPPORTED_MEDIA_TYPE", "File signature and MIME must agree")
                if max(width, height) > 16384 or width * height > 40_000_000 or getattr(image, "n_frames", 1) != 1:
                    raise ValueError()
                image.verify()
            stream.seek(0)
            with Image.open(stream) as image:
                image.load()
            stream.seek(0)
            return ImageFacts(width, height, actual, "png" if kind == "PNG" else "jpg")
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise DomainError(422, "INVALID_IMAGE", "Invalid, truncated, animated or oversized image", "file", "image validation failed") from None
