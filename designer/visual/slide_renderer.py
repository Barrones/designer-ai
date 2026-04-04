"""
Slide Renderer — gera slides internos do carrossel (slides 2–7).

Design: fundo escuro com gradiente sutil, número grande em accent,
headline em Bebas Neue, body em Inter, barra lateral em accent color.
"""
from __future__ import annotations

import os
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw

from designer import config
from designer.visual import renderer
from designer.copy.slides import SlideContent

Color = Tuple[int, int, int]

# Layout dos slides internos
_BG_TOP    = (12, 12, 18)      # fundo quase preto, leve azul
_BG_BOTTOM = (6, 6, 10)        # fundo mais escuro na base
_NUMBER_ALPHA = 18              # opacidade do número grande de fundo (fantasma)

_PAD_X = 64                    # margem horizontal
_PAD_Y = 80                    # margem vertical topo

_LABEL_SIZE   = 22
_NUMBER_SIZE  = 320             # número fantasma de fundo
_HEADLINE_SIZE = 86
_BODY_SIZE     = 34
_LINE_H_BODY   = 48


def render_slide(
    slide: SlideContent,
    accent_color: Color,
    handle: str,
    output_path: str | None = None,
) -> Image.Image:
    """
    Renderiza um slide interno (1080×1350).

    Parameters
    ----------
    slide        : SlideContent com número, headline, body, label
    accent_color : cor de destaque da marca (RGB)
    handle       : @handle da marca
    output_path  : se fornecido, salva o PNG
    """
    W, H = config.CANVAS_W, config.CANVAS_H

    # ------------------------------------------------------------------
    # 1. Fundo — gradiente vertical escuro
    # ------------------------------------------------------------------
    canvas = _make_dark_bg(W, H)

    # ------------------------------------------------------------------
    # 2. Número fantasma de fundo (grande, baixa opacidade)
    # ------------------------------------------------------------------
    _draw_ghost_number(canvas, str(slide.number), accent_color, W, H)

    # ------------------------------------------------------------------
    # 3. Header e footer — mesmos da capa
    # ------------------------------------------------------------------
    header = renderer.make_h_gradient(W, config.HEADER_H, config.GRADIENT_LEFT, config.GRADIENT_RIGHT)
    footer = renderer.make_h_gradient(W, config.FOOTER_H, config.GRADIENT_LEFT, config.GRADIENT_RIGHT)
    canvas.paste(header, (0, 0))
    canvas.paste(footer, (0, H - config.FOOTER_H))

    draw = ImageDraw.Draw(canvas)

    # ------------------------------------------------------------------
    # 4. Header UI text
    # ------------------------------------------------------------------
    ui_font = renderer.load_font(config.FONT_UI_LIGHT, config.FONT_SIZE_UI)
    bar_cy  = config.HEADER_H // 2
    draw.text((_PAD_X, bar_cy),     "Designer AI",      font=ui_font, fill=config.WHITE, anchor="lm")
    draw.text((W // 2, bar_cy),     handle,              font=ui_font, fill=config.WHITE, anchor="mm")
    draw.text((W - _PAD_X, bar_cy), f"0{slide.number}/07 //", font=ui_font, fill=config.WHITE, anchor="rm")

    # ------------------------------------------------------------------
    # 5. Barra lateral accent (esquerda)
    # ------------------------------------------------------------------
    bar_top = config.HEADER_H + _PAD_Y
    bar_bot = H - config.FOOTER_H - _PAD_Y
    draw.rectangle([_PAD_X - 24, bar_top, _PAD_X - 18, bar_bot], fill=accent_color + (255,))

    # ------------------------------------------------------------------
    # 6. Label
    # ------------------------------------------------------------------
    label_font = renderer.load_font(config.FONT_UI, _LABEL_SIZE)
    y = config.HEADER_H + _PAD_Y

    if slide.label:
        draw.text((_PAD_X, y), slide.label, font=label_font, fill=accent_color + (255,), anchor="lt")
        y += 40

    # ------------------------------------------------------------------
    # 7. Headline
    # ------------------------------------------------------------------
    hl_font   = renderer.load_font(config.FONT_HEADLINE, _HEADLINE_SIZE)
    max_text_w = W - 2 * _PAD_X

    lines = renderer.wrap_text(slide.headline, hl_font, max_text_w)
    y = renderer.draw_text_block(draw, lines, _PAD_X, y, hl_font, config.WHITE, _HEADLINE_SIZE + 8)
    y += 32

    # ------------------------------------------------------------------
    # 8. Divisor
    # ------------------------------------------------------------------
    draw.rectangle([_PAD_X, y, _PAD_X + 60, y + 4], fill=accent_color + (255,))
    y += 28

    # ------------------------------------------------------------------
    # 9. Body text
    # ------------------------------------------------------------------
    body_font  = renderer.load_font(config.FONT_UI, _BODY_SIZE)
    body_lines = _wrap_body(slide.body, body_font, draw, max_text_w)
    for line in body_lines:
        draw.text((_PAD_X, y), line, font=body_font, fill=(200, 200, 210), anchor="lt")
        y += _LINE_H_BODY

    # ------------------------------------------------------------------
    # 10. Salva
    # ------------------------------------------------------------------
    result = canvas.convert("RGB")
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result.save(output_path, "PNG", quality=95, optimize=True)

    return result


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _make_dark_bg(W: int, H: int) -> Image.Image:
    """Fundo escuro com gradiente vertical sutil."""
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    for c, (top_val, bot_val) in enumerate(zip(_BG_TOP, _BG_BOTTOM)):
        col = np.linspace(top_val, bot_val, H, dtype=np.float32).astype(np.uint8)
        arr[:, :, c] = col[:, np.newaxis]
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


def _draw_ghost_number(canvas: Image.Image, number: str, accent: Color, W: int, H: int) -> None:
    """Desenha o número grande em baixa opacidade como elemento gráfico de fundo."""
    try:
        ghost_font = renderer.load_font(config.FONT_HEADLINE, _NUMBER_SIZE)
        ghost_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ghost_draw  = ImageDraw.Draw(ghost_layer)
        ghost_draw.text(
            (W - 40, H // 2 + 60),
            number,
            font=ghost_font,
            fill=accent + (_NUMBER_ALPHA,),
            anchor="rm",
        )
        canvas.alpha_composite(ghost_layer)
    except Exception:
        pass


def _wrap_body(text: str, font, draw, max_width: int) -> list[str]:
    """Quebra o body text em linhas que cabem na largura."""
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
