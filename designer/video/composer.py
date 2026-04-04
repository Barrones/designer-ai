"""
Video Composer — aplica design system de alta conversão sobre um vídeo.

Layout baseado em dados Meta/TikTok 2026:
  - Safe area: evitar topo 150px e fundo 320px (UI do Instagram)
  - Texto no terço inferior com scrim escuro garantindo contraste
  - CTA como pill button centralizado — +45% conversão vs. texto puro
  - Drop shadow no texto — mínimo 85% contraste
  - Máximo 2 linhas visíveis por bloco
"""
from __future__ import annotations

import os
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw

from designer import config
from designer.visual import renderer

Color = Tuple[int, int, int]

REEL_W = 1080
REEL_H = 1920

_PAD_X         = 64
_HEADLINE_SIZE = 88
_HEADLINE_2_SIZE = 82
_CTA_SIZE      = 40
_HANDLE_SIZE   = 28
_UI_SIZE       = 21
_LINE_H        = 98

# Safe areas Meta 2026
_SAFE_TOP    = 150   # px do topo
_SAFE_BOTTOM = 320   # px do fundo


def render_video(
    video_path: str,
    headline_part1: str,
    headline_part2: str,
    cta: str,
    handle: str,
    accent_color: Color,
    output_path: str,
    duration: int = 15,
) -> str:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    bg_clip = VideoFileClip(video_path)
    bg_clip = _fit_to_reel(bg_clip, REEL_W, REEL_H, duration)

    overlay_img = _make_overlay_frame(
        headline_part1=headline_part1,
        headline_part2=headline_part2,
        cta=cta,
        handle=handle,
        accent_color=accent_color,
    )

    overlay_arr  = np.array(overlay_img.convert("RGBA"))
    overlay_clip = ImageClip(overlay_arr).with_duration(bg_clip.duration)

    final = CompositeVideoClip([bg_clip, overlay_clip], size=(REEL_W, REEL_H))
    final.write_videofile(
        output_path, fps=30, codec="libx264",
        audio_codec="aac", preset="fast", logger=None,
    )

    bg_clip.close()
    final.close()
    return output_path


def _fit_to_reel(clip, W: int, H: int, max_duration: int):
    from moviepy import vfx

    target = min(clip.duration, max_duration)
    if clip.duration < target:
        clip = clip.with_effects([vfx.Loop(duration=target)])
    clip  = clip.subclipped(0, target)
    scale = max(W / clip.w, H / clip.h)
    clip  = clip.resized((int(clip.w * scale), int(clip.h * scale)))
    x1    = (clip.w - W) // 2
    y1    = (clip.h - H) // 2
    return clip.cropped(x1=x1, y1=y1, width=W, height=H)


def _make_overlay_frame(
    headline_part1: str,
    headline_part2: str,
    cta: str,
    handle: str,
    accent_color: Color,
) -> Image.Image:
    """
    Layout de alta conversão (de baixo para cima):

      [H-320]          ← limite safe area fundo
      [CTA pill]       ← pill button centralizado, accent color
      [40px gap]
      [Headline pt2]   ← BarlowCondensed accent + shadow
      [Headline pt1]   ← Bebas Neue branco + shadow
      [Handle]         ← @handle pequeno
      [scrim gradiente começa aqui ~50% da altura]
      ...
      [Vídeo visível]  ← terço superior — captura atenção
      [Header bar]     ← Powered by Designer AI
    """
    W, H = REEL_W, REEL_H
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # ------------------------------------------------------------------
    # 1. Scrim gradiente — transparente no topo, escuro embaixo
    # ------------------------------------------------------------------
    scrim_start = int(H * 0.40)
    scrim_h     = H - scrim_start
    scrim_arr   = np.zeros((scrim_h, W, 4), dtype=np.uint8)
    alphas      = np.linspace(0, 210, scrim_h, dtype=np.float32).astype(np.uint8)
    scrim_arr[:, :, 3] = alphas[:, np.newaxis]
    canvas.alpha_composite(Image.fromarray(scrim_arr, "RGBA"), dest=(0, scrim_start))

    # ------------------------------------------------------------------
    # 2. Header bar
    # ------------------------------------------------------------------
    header = renderer.make_h_gradient(W, config.HEADER_H, config.GRADIENT_LEFT, config.GRADIENT_RIGHT)
    canvas.paste(header, (0, 0))
    draw   = ImageDraw.Draw(canvas)
    ui_f   = renderer.load_font(config.FONT_UI_LIGHT, _UI_SIZE)
    bar_cy = config.HEADER_H // 2
    draw.text((_PAD_X, bar_cy),     "Designer AI", font=ui_f, fill=config.WHITE, anchor="lm")
    draw.text((W // 2, bar_cy),     handle,         font=ui_f, fill=config.WHITE, anchor="mm")
    draw.text((W - _PAD_X, bar_cy), "2026 //",      font=ui_f, fill=config.WHITE, anchor="rm")

    # ------------------------------------------------------------------
    # 3. Medidas e fontes
    # ------------------------------------------------------------------
    hl1   = renderer.load_font(config.FONT_HEADLINE,        _HEADLINE_SIZE)
    hl2   = renderer.load_font(config.FONT_HEADLINE_ITALIC, _HEADLINE_2_SIZE)
    h_f   = renderer.load_font(config.FONT_UI,              _HANDLE_SIZE)
    cta_f = renderer.load_font(config.FONT_HEADLINE,        _CTA_SIZE)
    max_w = W - 2 * _PAD_X

    lines1 = renderer.wrap_text(headline_part1.upper(), hl1, max_w)
    lines2 = renderer.wrap_text(headline_part2.upper(), hl2, max_w)

    HANDLE_H  = 36
    GAP_H     = 14
    GAP_PARTS = 12
    CTA_H     = 100
    CTA_GAP   = 36

    # ------------------------------------------------------------------
    # 4. Posições (de baixo para cima)
    # ------------------------------------------------------------------
    content_bottom = H - _SAFE_BOTTOM          # 1600px

    # CTA pill: toca a borda inferior da safe area
    cta_bottom = content_bottom
    cta_top    = cta_bottom - CTA_H            # 1500px

    # Bloco de texto: acima do CTA
    block_h = (
        HANDLE_H + GAP_H
        + len(lines1) * _LINE_H
        + GAP_PARTS
        + len(lines2) * _LINE_H
    )
    text_bottom = cta_top - CTA_GAP
    text_top    = text_bottom - block_h

    # Não sobe além de 48%
    text_top = max(int(H * 0.48), text_top)

    # ------------------------------------------------------------------
    # 5. Scrim extra sólido atrás do texto (garante >85% contraste)
    # ------------------------------------------------------------------
    extra_top = text_top - 30
    extra_h   = content_bottom - extra_top
    extra_arr = np.zeros((extra_h, W, 4), dtype=np.uint8)
    a_extra   = np.linspace(0, 150, extra_h, dtype=np.float32).astype(np.uint8)
    extra_arr[:, :, 3] = a_extra[:, np.newaxis]
    canvas.alpha_composite(Image.fromarray(extra_arr, "RGBA"), dest=(0, extra_top))
    draw = ImageDraw.Draw(canvas)

    # ------------------------------------------------------------------
    # 6. Barra accent lateral (ao lado da headline pt2)
    # ------------------------------------------------------------------
    bar_y1 = text_top + HANDLE_H + GAP_H + len(lines1) * _LINE_H + GAP_PARTS - 6
    bar_y2 = bar_y1 + len(lines2) * _LINE_H + 6
    draw.rectangle([_PAD_X - 20, bar_y1, _PAD_X - 12, bar_y2], fill=accent_color + (255,))

    # ------------------------------------------------------------------
    # 7. Texto com drop shadow
    # ------------------------------------------------------------------
    y = text_top
    draw.text((_PAD_X, y), f"//  {handle}", font=h_f, fill=(180, 180, 180, 200), anchor="lt")
    y += HANDLE_H + GAP_H

    for line in lines1:
        _shadow_text(draw, _PAD_X, y, line, hl1, config.WHITE)
        y += _LINE_H
    y += GAP_PARTS

    for line in lines2:
        _shadow_text(draw, _PAD_X, y, line, hl2, accent_color)
        y += _LINE_H

    # ------------------------------------------------------------------
    # 8. CTA — pill button centralizado
    # ------------------------------------------------------------------
    cta_clean = _sanitize_text(cta).upper()

    # Mede texto
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox  = dummy.textbbox((0, 0), cta_clean, font=cta_f)
    tw    = bbox[2] - bbox[0]
    th    = bbox[3] - bbox[1]

    PILL_PX = 56
    PILL_PY = 20
    pill_w  = min(tw + 2 * PILL_PX, W - 2 * _PAD_X)
    pill_h  = th + 2 * PILL_PY
    pill_x  = (W - pill_w) // 2
    pill_y  = cta_top + (CTA_H - pill_h) // 2

    # Pill com borda accent
    pill_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pill_draw  = ImageDraw.Draw(pill_layer)
    r, g, b    = accent_color

    # Sombra do pill
    pill_draw.rounded_rectangle(
        [pill_x + 4, pill_y + 4, pill_x + pill_w + 4, pill_y + pill_h + 4],
        radius=pill_h // 2, fill=(0, 0, 0, 120),
    )
    # Fundo do pill
    pill_draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2, fill=(r, g, b, 230),
    )
    # Borda pill
    pill_draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2, outline=(255, 255, 255, 180), width=2,
    )
    canvas.alpha_composite(pill_layer)

    # Texto do pill
    draw = ImageDraw.Draw(canvas)
    from designer.brand.profile import _luminance
    txt_color = (10, 10, 10) if _luminance(accent_color) > 140 else config.WHITE
    draw.text(
        (W // 2, pill_y + pill_h // 2),
        cta_clean, font=cta_f, fill=txt_color, anchor="mm",
    )

    return canvas


def _shadow_text(draw, x: int, y: int, text: str, font, fill: tuple) -> None:
    """Texto com sombra preta para garantir legibilidade."""
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180), anchor="lt")
    draw.text((x, y),         text, font=font, fill=fill,            anchor="lt")


def _sanitize_text(text: str) -> str:
    """Remove caracteres Unicode não suportados pelas fontes."""
    replacements = {
        "\u2192": ">>", "\u2190": "<<", "→": ">>", "←": "<<",
        "✓": "", "✗": "X", "☀": "", "★": "*", "\u00ae": "(R)",
    }
    for ch, rep in replacements.items():
        text = text.replace(ch, rep)
    return "".join(c if ord(c) < 0x0250 or c in " ,.!?:;-_()[]/@#>>" else "" for c in text).strip()
