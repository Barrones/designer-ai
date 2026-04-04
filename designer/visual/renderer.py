"""Low-level Pillow rendering utilities used by all visual generators."""
from __future__ import annotations

import os
from io import BytesIO
from typing import Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

Color = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------

def load_image(source: str, size: Tuple[int, int]) -> Image.Image:
    """Load an image from a URL or local path, scale+crop to fill *size*."""
    if source.startswith("http://") or source.startswith("https://"):
        resp = requests.get(source, timeout=20)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
    else:
        img = Image.open(source).convert("RGBA")
    return _cover_crop(img, size)


def _cover_crop(img: Image.Image, target: Tuple[int, int]) -> Image.Image:
    """Scale image to cover *target*, then center-crop."""
    tw, th = target
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw) // 2
    top  = (new_h - th) // 2
    return img.crop((left, top, left + tw, top + th))


# ---------------------------------------------------------------------------
# Gradient helpers
# ---------------------------------------------------------------------------

def make_h_gradient(
    width: int,
    height: int,
    left: Color,
    right: Color,
) -> Image.Image:
    """Horizontal RGB gradient image."""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    for c in range(3):
        arr[:, :, c] = np.linspace(left[c], right[c], width, dtype=np.float32).astype(np.uint8)
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def make_v_overlay(
    width: int,
    height: int,
    alpha_top: int = 0,
    alpha_bottom: int = 200,
) -> Image.Image:
    """Vertical black gradient overlay — transparent at top, dark at bottom."""
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    alphas = np.linspace(alpha_top, alpha_bottom, height, dtype=np.float32).astype(np.uint8)
    arr[:, :, 3] = alphas[:, np.newaxis]
    return Image.fromarray(arr, "RGBA")


# ---------------------------------------------------------------------------
# Font loading
# ---------------------------------------------------------------------------

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType font or raise a clear error pointing to setup_fonts.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Font not found: {path}\n"
            "Run:  python setup_fonts.py"
        )
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Word-wrap *text* so each line fits within *max_width* pixels."""
    dummy = Image.new("RGBA", (1, 1))
    draw  = ImageDraw.Draw(dummy)

    words   = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines


def text_block_height(
    lines: list[str],
    line_height: int,
) -> int:
    """Total pixel height of a block of *lines*."""
    return len(lines) * line_height


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: Color | Tuple[int, int, int, int],
    line_height: int,
    anchor: str = "lt",
) -> int:
    """Draw *lines* starting at (x, y). Returns the y position after the last line."""
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, anchor=anchor)
        y += line_height
    return y
