"""Carousel cover renderer — produces a 1080×1350 PNG matching BrandsDecoded style."""
from __future__ import annotations

import os
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from designer import config
from designer.visual import renderer

Color = Tuple[int, int, int]

# Extra padding inside the text zone
_TEXT_ZONE_PAD_TOP    = 32   # px above handle text
_TEXT_ZONE_PAD_BOTTOM = 28   # px below last headline line
_TEXT_ZONE_PAD_SIDES  = 36   # px left/right inside dark strip


def render_cover(
    headline_part1: str,
    headline_part2: str,
    handle: str,
    image_source: str,
    accent_color: Color = config.ACCENT_RED,
    powered_by: str = "Designer AI",
    year: int = 2026,
    output_path: Optional[str] = None,
) -> Image.Image:
    """
    Render a single carousel cover image (1080×1350).

    headline_part1  → white Anton (setup/context)
    headline_part2  → accent_color + BarlowCondensed BoldItalic (provocação)
    """
    W, H = config.CANVAS_W, config.CANVAS_H
    pad  = config.PAD_X

    # -----------------------------------------------------------------------
    # 1. Background image — full bleed, center-cropped
    # -----------------------------------------------------------------------
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    bg = renderer.load_image(image_source, (W, H))
    canvas.paste(bg, (0, 0))

    # -----------------------------------------------------------------------
    # 2. Strong full-canvas dark overlay (vignette style)
    #    Top stays lighter; bottom is near-opaque so text is always readable
    # -----------------------------------------------------------------------
    overlay = renderer.make_v_overlay(W, H, alpha_top=30, alpha_bottom=235)
    canvas.alpha_composite(overlay)

    # -----------------------------------------------------------------------
    # 3. Header bar
    # -----------------------------------------------------------------------
    header = renderer.make_h_gradient(W, config.HEADER_H, config.GRADIENT_LEFT, config.GRADIENT_RIGHT)
    canvas.paste(header, (0, 0))

    # -----------------------------------------------------------------------
    # 4. Footer bar
    # -----------------------------------------------------------------------
    footer = renderer.make_h_gradient(W, config.FOOTER_H, config.GRADIENT_LEFT, config.GRADIENT_RIGHT)
    canvas.paste(footer, (0, H - config.FOOTER_H))

    draw = ImageDraw.Draw(canvas)

    # -----------------------------------------------------------------------
    # 5. Header UI text
    # -----------------------------------------------------------------------
    ui_font = renderer.load_font(config.FONT_UI_LIGHT, config.FONT_SIZE_UI)
    bar_cy  = config.HEADER_H // 2

    draw.text((pad, bar_cy),     f"Powered by {powered_by}", font=ui_font, fill=config.WHITE, anchor="lm")
    draw.text((W // 2, bar_cy),  handle,                     font=ui_font, fill=config.WHITE, anchor="mm")
    draw.text((W - pad, bar_cy), f"{year} //",               font=ui_font, fill=config.WHITE, anchor="rm")

    # -----------------------------------------------------------------------
    # 6. Load fonts
    # -----------------------------------------------------------------------
    hl_font_1 = renderer.load_font(config.FONT_HEADLINE,        config.FONT_SIZE_HEADLINE)
    hl_font_2 = renderer.load_font(config.FONT_HEADLINE_ITALIC, config.FONT_SIZE_ITALIC)
    h_font    = renderer.load_font(config.FONT_UI,              config.FONT_SIZE_HANDLE)

    max_text_w = W - 2 * pad - 2 * _TEXT_ZONE_PAD_SIDES

    # -----------------------------------------------------------------------
    # 7. Word-wrap
    # -----------------------------------------------------------------------
    lines1 = renderer.wrap_text(headline_part1.upper(), hl_font_1, max_text_w)
    lines2 = renderer.wrap_text(headline_part2.upper(), hl_font_2, max_text_w)

    lh = config.LINE_HEIGHT_HEADLINE

    handle_h = 44
    gap_handle = 16
    gap_parts  = 10

    total_text_h = (
        _TEXT_ZONE_PAD_TOP
        + handle_h + gap_handle
        + len(lines1) * lh
        + gap_parts
        + len(lines2) * lh
        + _TEXT_ZONE_PAD_BOTTOM
    )

    # Anchor: start at 58% of canvas height, push up if overflow
    y_zone_top = int(H * 0.58)
    footer_top = H - config.FOOTER_H - 16
    if y_zone_top + total_text_h > footer_top:
        y_zone_top = max(config.HEADER_H + 16, footer_top - total_text_h)

    y_zone_bottom = y_zone_top + total_text_h

    # -----------------------------------------------------------------------
    # 8. Dark semi-transparent strip behind the entire text block
    #    Ensures 100% legibility regardless of background photo
    # -----------------------------------------------------------------------
    strip = Image.new("RGBA", (W, y_zone_bottom - y_zone_top), (0, 0, 0, 0))
    strip_arr = np.array(strip)
    # Gradient: fully transparent at top → 80% black at bottom
    alphas = np.linspace(0, 200, strip_arr.shape[0], dtype=np.float32).astype(np.uint8)
    strip_arr[:, :, 3] = alphas[:, np.newaxis]
    strip_img = Image.fromarray(strip_arr, "RGBA")
    canvas.alpha_composite(strip_img, dest=(0, y_zone_top))

    # -----------------------------------------------------------------------
    # 9. Accent color bar — thin left edge marker for headline pt2 (design detail)
    # -----------------------------------------------------------------------
    bar_x  = pad - 16
    bar_y1 = y_zone_top + _TEXT_ZONE_PAD_TOP + handle_h + gap_handle + len(lines1) * lh + gap_parts - 4
    bar_y2 = bar_y1 + len(lines2) * lh + 4
    draw.rectangle([bar_x, bar_y1, bar_x + 5, bar_y2], fill=accent_color + (255,))

    # -----------------------------------------------------------------------
    # 10. Text rendering
    # -----------------------------------------------------------------------
    tx = pad + _TEXT_ZONE_PAD_SIDES   # text x with zone padding
    y  = y_zone_top + _TEXT_ZONE_PAD_TOP

    # @handle + badge
    draw.text((tx, y), f"☀  {handle}  ✓", font=h_font, fill=config.WHITE, anchor="lt")
    y += handle_h + gap_handle

    # Headline part 1 — white Anton
    y = renderer.draw_text_block(draw, lines1, tx, y, hl_font_1, config.WHITE, lh)
    y += gap_parts

    # Headline part 2 — accent + BarlowCondensed BoldItalic
    renderer.draw_text_block(draw, lines2, tx, y, hl_font_2, accent_color, lh)

    # -----------------------------------------------------------------------
    # 11. Save / return
    # -----------------------------------------------------------------------
    result = canvas.convert("RGB")
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.save(output_path, "PNG", quality=95, optimize=True)
        print(f"✓ Saved: {output_path}")

    return result
