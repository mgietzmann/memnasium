"""Normalising an upload before it is stored — design/Stack.md.

    whatever was pasted  →  decode  →  longest side ≤ 1600px  →  WebP  →  data/images/{img_id}.webp

The server converts rather than rejects, so the format is an internal fact rather than something
the player has to get right. Nothing else is stored — no original, no thumbnail.
"""

import io
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from api import paths
from api.errors import bad_request

MAX_SIDE = 1600
"""Enough to tell fish apart on screen, and a file in the low hundreds of kilobytes."""

QUALITY = 82


def store_image(data: bytes) -> str:
    """Convert an uploaded image to WebP, scale it down, and write it under a fresh id.

    Args:
        data: The bytes as uploaded, in any format Pillow can decode.

    Returns:
        The `img_id`, which is also the filename stem.

    Raises:
        ApiError: 400 when the upload is not a decodable image.
    """
    try:
        with Image.open(io.BytesIO(data)) as opened:
            opened.load()
            image = opened.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise bad_request("upload is not a decodable image") from exc

    longest = max(image.size)
    if longest > MAX_SIDE:
        scale = MAX_SIDE / longest
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )

    img_id = uuid4().hex
    paths.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image.save(paths.image_path(img_id), format="WEBP", quality=QUALITY)
    return img_id
