"""
Slide Renderer — gera slides internos do carrossel (Pillow).

Design atualizado: alternância dark/light conforme Designer AI Design System.
- Dark: fundo escuro, headlines brancas, ghost number
- Light: fundo claro, headlines escuras, cards brancos
- Gradient: fundo gradiente da marca
- Progress bar e accent bar em todos os slides
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from designer import config
from designer.visual import renderer

Color = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_PAD_X = 56             # margem horizontal (safe area)
_PAD_Y_TOP = 110        # topo da área de conteúdo
_PAD_Y_BOTTOM = 80      # padding antes da progress bar
_ACCENT_BAR_H = 7       # accent bar no topo
_PROGRESS_BAR_H = 3     # progress bar track
_PROGRESS_BOTTOM = 30   # distância do fundo

# Font sizes
_TAG_SIZE = 22
_HEADLINE_SIZE_DARK = 80
_HEADLINE_SIZE_LIGHT = 72
_HEADLINE_SIZE_GRAD = 80
_BODY_SIZE = 36
_LINE_H_BODY = 54
_BRAND_BAR_SIZE = 14
_PROGRESS_SIZE = 15
_GHOST_SIZE = 380


def render_slide(
    slide,
    accent_color: Color,
    handle: str,
    palette: Optional[dict] = None,
    total_slides: int = 9,
    brand_name: str = "Designer AI",
    year: int = 2026,
    image_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Image.Image:
    """
    Renderiza um slide interno (1080×1350).

    Parameters
    ----------
    slide        : SlideContent (number, type, theme, tag, headline, body, body2)
    accent_color : cor de destaque da marca (RGB)
    handle       : @handle da marca
    palette      : dict from config.derive_palette() (optional, for light bg colors)
    total_slides : total de slides no carrossel
    brand_name   : nome da marca
    year         : ano para brand bar
    image_path   : caminho para imagem de fundo (dark slides) ou img-box (light slides)
    output_path  : se fornecido, salva o PNG
    """
    W, H = config.CANVAS_W, config.CANVAS_H
    theme = getattr(slide, "theme", "dark")

    if theme == "dark":
        canvas = _render_dark_slide(slide, W, H, accent_color, handle, palette,
                                     total_slides, brand_name, year, image_path)
    elif theme == "light":
        canvas = _render_light_slide(slide, W, H, accent_color, handle, palette,
                                      total_slides, brand_name, year, image_path)
    elif theme == "gradient":
        canvas = _render_gradient_slide(slide, W, H, accent_color, handle, palette,
                                         total_slides, brand_name, year)
    else:
        canvas = _render_dark_slide(slide, W, H, accent_color, handle, palette,
                                     total_slides, brand_name, year, image_path)

    result = canvas.convert("RGB")
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.save(output_path, "PNG", quality=95, optimize=True)

    return result


# ---------------------------------------------------------------------------
# DARK SLIDE
# ---------------------------------------------------------------------------

def _render_dark_slide(slide, W, H, accent, handle, palette, total, brand_name, year, image_path):
    dark_bg = palette["dark_bg"] if palette else (15, 13, 12)
    canvas = _make_bg(W, H, dark_bg)

    # Background image with overlay (if provided)
    if image_path and os.path.exists(image_path):
        bg = renderer.load_image(image_path, (W, H))
        canvas.paste(bg, (0, 0))
        overlay = renderer.make_v_overlay(W, H, alpha_top=204, alpha_bottom=230)
        canvas.alpha_composite(overlay)

    # Ghost number
    _draw_ghost_number(canvas, str(slide.number), accent, W, H)

    # Accent bar
    _draw_accent_bar(canvas, W, accent, palette)

    draw = ImageDraw.Draw(canvas)

    # Brand bar
    _draw_brand_bar(draw, W, handle, brand_name, year, config.WHITE, alpha=115)

    # Content area — flex-end (start from bottom)
    y_bottom = H - _PAD_Y_BOTTOM - _PROGRESS_BOTTOM - 20
    y = y_bottom

    # Body (rendered from bottom up)
    if slide.body:
        body_font = renderer.load_font(config.FONT_UI, _BODY_SIZE)
        body_lines = _wrap_text(slide.body, body_font, draw, W - 2 * _PAD_X)
        y -= len(body_lines) * _LINE_H_BODY
        body_y = y
        for line in body_lines:
            draw.text((_PAD_X, body_y), line, font=body_font, fill=(255, 255, 255, 140))
            body_y += _LINE_H_BODY
        y -= 36  # gap before headline

    # Headline
    if slide.headline:
        hl_font = renderer.load_font(config.FONT_HEADLINE, _HEADLINE_SIZE_DARK)
        hl_lines = renderer.wrap_text(slide.headline.upper(), hl_font, W - 2 * _PAD_X)
        lh = _HEADLINE_SIZE_DARK + 4
        y -= len(hl_lines) * lh
        renderer.draw_text_block(draw, hl_lines, _PAD_X, y, hl_font, config.WHITE, lh)
        y -= 24

    # Tag
    if slide.tag:
        tag_font = renderer.load_font(config.FONT_UI, _TAG_SIZE)
        y -= 30
        draw.text((_PAD_X, y), slide.tag.upper(), font=tag_font, fill=accent + (255,))

    # Progress bar
    _draw_progress_bar(draw, canvas, W, H, slide.number, total, "dark", accent)

    return canvas


# ---------------------------------------------------------------------------
# LIGHT SLIDE
# ---------------------------------------------------------------------------

def _render_light_slide(slide, W, H, accent, handle, palette, total, brand_name, year, image_path):
    light_bg = palette["light_bg"] if palette else (245, 242, 239)
    dark_text = palette["dark_bg"] if palette else (15, 13, 12)
    canvas = _make_bg(W, H, light_bg)

    # Accent bar
    _draw_accent_bar(canvas, W, accent, palette)

    draw = ImageDraw.Draw(canvas)

    # Brand bar
    _draw_brand_bar(draw, W, handle, brand_name, year, dark_text, alpha=115)

    # Content area — flex-end
    y_bottom = H - _PAD_Y_BOTTOM - _PROGRESS_BOTTOM - 20
    y = y_bottom

    # Image box (if provided)
    img_box_h = 0
    if image_path and os.path.exists(image_path):
        img = renderer.load_image(image_path, (W - 2 * _PAD_X, 360))
        # We'll render this at the top of content area later
        img_box_h = 360 + 36

    # Body
    if slide.body:
        body_font = renderer.load_font(config.FONT_UI, _BODY_SIZE)
        body_lines = _wrap_text(slide.body, body_font, draw, W - 2 * _PAD_X)
        y -= len(body_lines) * _LINE_H_BODY
        body_y = y
        body_color = (15, 13, 12, 153)  # rgba(15,13,12,0.60)
        for line in body_lines:
            draw.text((_PAD_X, body_y), line, font=body_font, fill=body_color)
            body_y += _LINE_H_BODY
        y -= 32

    # Headline
    if slide.headline:
        hl_font = renderer.load_font(config.FONT_HEADLINE, _HEADLINE_SIZE_LIGHT)
        hl_lines = renderer.wrap_text(slide.headline.upper(), hl_font, W - 2 * _PAD_X)
        lh = _HEADLINE_SIZE_LIGHT + 4
        y -= len(hl_lines) * lh
        renderer.draw_text_block(draw, hl_lines, _PAD_X, y, hl_font, dark_text, lh)
        y -= 24

    # Tag
    if slide.tag:
        tag_font = renderer.load_font(config.FONT_UI, _TAG_SIZE)
        y -= 30
        draw.text((_PAD_X, y), slide.tag.upper(), font=tag_font, fill=accent + (255,))

    # Image box rendered at top of content
    if image_path and os.path.exists(image_path) and img_box_h > 0:
        img = renderer.load_image(image_path, (W - 2 * _PAD_X, 360))
        img_y = _PAD_Y_TOP
        # Round corners (approximate with paste)
        canvas.paste(img.convert("RGB"), (_PAD_X, img_y))

    # Progress bar
    _draw_progress_bar(draw, canvas, W, H, slide.number, total, "light", accent)

    return canvas


# ---------------------------------------------------------------------------
# GRADIENT SLIDE
# ---------------------------------------------------------------------------

def _render_gradient_slide(slide, W, H, accent, handle, palette, total, brand_name, year):
    # Create gradient background
    primary = palette["primary"] if palette else accent
    primary_dark = palette["primary_dark"] if palette else (0, 0, 0)
    primary_light = palette["primary_light"] if palette else accent

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    arr = np.array(canvas)

    for c in range(3):
        col = np.linspace(primary_dark[c], primary_light[c], H, dtype=np.float32)
        arr[:, :, c] = col[:, np.newaxis].astype(np.uint8)
    arr[:, :, 3] = 255
    canvas = Image.fromarray(arr, "RGBA")

    # Ghost number
    _draw_ghost_number(canvas, str(slide.number), (255, 255, 255), W, H, alpha=15)

    # Accent bar (white semi-transparent on gradient)
    accent_bar = Image.new("RGBA", (W, _ACCENT_BAR_H), (255, 255, 255, 46))
    canvas.alpha_composite(accent_bar, dest=(0, 0))

    draw = ImageDraw.Draw(canvas)

    # Brand bar
    _draw_brand_bar(draw, W, handle, brand_name, year, config.WHITE, alpha=128)

    # Content — flex-end
    y_bottom = H - _PAD_Y_BOTTOM - _PROGRESS_BOTTOM - 20
    y = y_bottom

    # Body
    if slide.body:
        body_font = renderer.load_font(config.FONT_UI, _BODY_SIZE)
        body_lines = _wrap_text(slide.body, body_font, draw, W - 2 * _PAD_X)
        y -= len(body_lines) * _LINE_H_BODY
        body_y = y
        for line in body_lines:
            draw.text((_PAD_X, body_y), line, font=body_font, fill=(255, 255, 255, 166))
            body_y += _LINE_H_BODY
        y -= 40

    # Headline
    if slide.headline:
        hl_font = renderer.load_font(config.FONT_HEADLINE, _HEADLINE_SIZE_GRAD)
        hl_lines = renderer.wrap_text(slide.headline.upper(), hl_font, W - 2 * _PAD_X)
        lh = _HEADLINE_SIZE_GRAD + 4
        y -= len(hl_lines) * lh
        renderer.draw_text_block(draw, hl_lines, _PAD_X, y, hl_font, config.WHITE, lh)
        y -= 24

    # Tag
    if slide.tag:
        tag_font = renderer.load_font(config.FONT_UI, _TAG_SIZE)
        y -= 30
        draw.text((_PAD_X, y), slide.tag.upper(), font=tag_font, fill=(255, 255, 255, 140))

    # Progress bar
    _draw_progress_bar(draw, canvas, W, H, slide.number, total, "gradient", accent)

    return canvas


# ---------------------------------------------------------------------------
# SHARED COMPONENTS
# ---------------------------------------------------------------------------

def _make_bg(W: int, H: int, color: Color) -> Image.Image:
    """Solid background."""
    canvas = Image.new("RGBA", (W, H), color + (255,))
    return canvas


def _draw_accent_bar(canvas: Image.Image, W: int, accent: Color, palette: Optional[dict]):
    """Draw gradient accent bar at top."""
    if palette:
        pd = palette["primary_dark"]
        p = palette["primary"]
        pl = palette["primary_light"]
    else:
        pd = accent
        p = accent
        pl = accent

    bar = Image.new("RGBA", (W, _ACCENT_BAR_H), (0, 0, 0, 0))
    arr = np.array(bar)
    for x_pos in range(W):
        t = x_pos / W
        if t < 0.5:
            t2 = t * 2
            c = tuple(int(pd[i] + (p[i] - pd[i]) * t2) for i in range(3))
        else:
            t2 = (t - 0.5) * 2
            c = tuple(int(p[i] + (pl[i] - p[i]) * t2) for i in range(3))
        arr[0:_ACCENT_BAR_H, x_pos, :3] = c
        arr[0:_ACCENT_BAR_H, x_pos, 3] = 255
    bar = Image.fromarray(arr, "RGBA")
    canvas.alpha_composite(bar, dest=(0, 0))


def _draw_brand_bar(draw, W, handle, brand_name, year, color, alpha=115):
    """Draw brand bar text below accent bar."""
    try:
        font = renderer.load_font(config.FONT_UI, _BRAND_BAR_SIZE)
    except Exception:
        return

    y = _ACCENT_BAR_H + 32
    text_color = color[:3] + (alpha,) if len(color) == 3 else color

    draw.text((_PAD_X, y), "POWERED BY DESIGNER AI", font=font, fill=text_color, anchor="lt")
    draw.text((W // 2, y), handle.upper(), font=font, fill=text_color, anchor="mt")
    draw.text((W - _PAD_X, y), f"{year} ®", font=font, fill=text_color, anchor="rt")


def _draw_progress_bar(draw, canvas, W, H, current, total, theme, accent):
    """Draw progress bar at bottom of slide."""
    try:
        font = renderer.load_font(config.FONT_UI, _PROGRESS_SIZE)
    except Exception:
        return

    bar_y = H - _PROGRESS_BOTTOM
    track_x1 = _PAD_X
    track_x2 = W - _PAD_X - 60  # leave space for counter
    track_w = track_x2 - track_x1
    fill_w = int(track_w * (current / total))

    if theme == "dark":
        track_color = (255, 255, 255, 26)   # rgba(255,255,255,0.10)
        fill_color = (255, 255, 255, 255)
        num_color = (255, 255, 255, 56)
    elif theme == "gradient":
        track_color = (255, 255, 255, 38)   # rgba(255,255,255,0.15)
        fill_color = (255, 255, 255, 153)
        num_color = (255, 255, 255, 77)
    else:  # light
        track_color = (0, 0, 0, 20)          # rgba(0,0,0,0.08)
        fill_color = accent + (255,)
        num_color = (0, 0, 0, 56)

    # Track
    track_layer = Image.new("RGBA", (track_w, _PROGRESS_BAR_H), track_color)
    canvas.alpha_composite(track_layer, dest=(track_x1, bar_y))

    # Fill
    if fill_w > 0:
        fill_layer = Image.new("RGBA", (fill_w, _PROGRESS_BAR_H), fill_color)
        canvas.alpha_composite(fill_layer, dest=(track_x1, bar_y))

    # Counter
    draw.text((W - _PAD_X, bar_y + 1), f"{current}/{total}", font=font, fill=num_color, anchor="rt")


def _draw_ghost_number(canvas, number, color, W, H, alpha=10):
    """Large ghost number in background."""
    try:
        ghost_font = renderer.load_font(config.FONT_HEADLINE, _GHOST_SIZE)
        ghost_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ghost_draw = ImageDraw.Draw(ghost_layer)
        ghost_draw.text(
            (W - 10, H - 50),
            number,
            font=ghost_font,
            fill=color + (alpha,),
            anchor="rb",
        )
        canvas.alpha_composite(ghost_layer)
    except Exception:
        pass


def _wrap_text(text: str, font, draw, max_width: int) -> list[str]:
    """Word-wrap text to fit width."""
    words = text.split()
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
