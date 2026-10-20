"""Small image helpers used to brand the Argon theme.

Pillow is used when available (it is installed by ``install-deps``) but every
function degrades to a pure-stdlib implementation so the customisation step
never fails because of a missing optional library.
"""

from __future__ import annotations

import base64
import io
import struct
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _pillow():
    try:
        from PIL import Image  # type: ignore

        return Image
    except Exception:  # noqa: BLE001
        return None


def png_size(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIGNATURE) or len(data) < 24:
        raise ValueError("not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def resize_png(data: bytes, size: int) -> bytes | None:
    Image = _pillow()
    if Image is None:
        return None
    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGBA")
        if image.size != (size, size):
            resample = getattr(Image, "Resampling", Image).LANCZOS
            image = image.resize((size, size), resample)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()


def jpeg_to_webp(data: bytes, quality: int = 90) -> bytes | None:
    Image = _pillow()
    if Image is None:
        return None
    with Image.open(io.BytesIO(data)) as image:
        output = io.BytesIO()
        image.save(output, format="WEBP", quality=quality, method=4)
        return output.getvalue()


def png_to_ico(data: bytes, sizes: tuple[int, ...] = (16, 32, 48, 64, 128, 256)) -> bytes:
    """Build a multi-resolution ICO file.

    With Pillow this produces real resized frames; without it the original
    PNG is embedded as a single frame, which Windows Vista+ and all modern
    browsers understand.
    """
    Image = _pillow()
    if Image is not None:
        with Image.open(io.BytesIO(data)) as image:
            image = image.convert("RGBA")
            output = io.BytesIO()
            image.save(output, format="ICO", sizes=[(size, size) for size in sizes])
            return output.getvalue()

    frames = []
    width, height = png_size(data)
    w_byte = 0 if width >= 256 else width
    h_byte = 0 if height >= 256 else height
    frames.append((w_byte, h_byte, data))

    header = struct.pack("<HHH", 0, 1, len(frames))
    entries = b""
    payload = b""
    offset = 6 + 16 * len(frames)
    for w_byte, h_byte, frame in frames:
        entries += struct.pack("<BBBBHHII", w_byte, h_byte, 0, 0, 1, 32, len(frame), offset)
        offset += len(frame)
        payload += frame
    return header + entries + payload


def svg_wrapper(png_data: bytes, dest: Path, *, size: int | None = None) -> None:
    """Write an SVG that renders the PNG, preserving the original filename.

    Argon references ``img/argon.svg`` from several templates, so replacing
    the file contents instead of the references keeps every template working.
    """
    width, height = png_size(png_data)
    if size:
        width = height = size
    encoded = base64.b64encode(png_data).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" '
        f'xlink:href="data:image/png;base64,{encoded}"/>\n'
        "</svg>\n"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg, encoding="utf-8")
