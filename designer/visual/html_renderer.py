"""
HTML Carousel Renderer — Designer AI Design System
Generates a single HTML file with all carousel slides (1080×1350px native).

Features:
- Alternating dark/light template
- Accent bar, brand bar, progress bar on every slide
- Cover with full-bleed image + gradient overlay
- Dark slides with ghost numbers
- Light slides with cards and tables
- Gradient slide for direction
- CTA slide with keyword box
- Preview mode (side-by-side miniatures) + full-size mode
- Fonts embedded as base64 for Playwright export consistency
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

from designer import config
from designer.copy.slides import SlideContent


def _encode_font_base64(font_path: str) -> str:
    """Read a .ttf/.woff2 file and return base64-encoded string."""
    if not os.path.exists(font_path):
        return ""
    with open(font_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _encode_image_base64(image_path: str) -> str:
    """Read an image file and return data URI."""
    if not image_path or not os.path.exists(image_path):
        return ""
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{b64}"


def render_html(
    slides: list[SlideContent],
    brand_name: str,
    handle: str,
    palette: dict,
    headline: str,
    cover_image: Optional[str] = None,
    slide_images: Optional[dict[int, str]] = None,
    font_headline: str = "Barlow Condensed",
    font_body: str = "Plus Jakarta Sans",
    year: int = 2026,
    output_path: Optional[str] = None,
) -> str:
    """
    Render complete carousel as a single HTML file.

    Parameters
    ----------
    slides         : list of SlideContent (all slides including capa and CTA)
    brand_name     : display name of the brand
    handle         : Instagram @handle
    palette        : dict from config.derive_palette()
    headline       : full headline for the cover
    cover_image    : path to cover image (will be base64-embedded)
    slide_images   : dict mapping slide number → image path
    font_headline  : headline font family name
    font_body      : body font family name
    year           : year for brand bar
    output_path    : if provided, saves the HTML file
    """
    if slide_images is None:
        slide_images = {}

    total_slides = len(slides)
    P = palette["primary_hex"]
    PL = palette["primary_light_hex"]
    PD = palette["primary_dark_hex"]
    LB = palette["light_bg_hex"]
    LR = palette["light_border_hex"]
    DB = palette["dark_bg_hex"]
    G = palette["gradient_css"]

    # Encode cover image
    cover_b64 = _encode_image_base64(cover_image) if cover_image else ""

    # Encode slide images
    slide_imgs_b64 = {}
    for num, path in slide_images.items():
        slide_imgs_b64[num] = _encode_image_base64(path)

    # Encode fonts if available locally
    fonts_css = _build_fonts_css(font_headline, font_body)

    # Build slides HTML
    slides_html = []
    for i, slide in enumerate(slides):
        slide_num = i + 1
        progress_pct = (slide_num / total_slides) * 100
        img_b64 = slide_imgs_b64.get(slide_num, "")

        if slide.theme == "capa":
            slides_html.append(_render_capa(
                slide, slide_num, total_slides, progress_pct,
                handle, brand_name, year, headline, cover_b64, P, PL, G,
            ))
        elif slide.theme == "dark":
            slides_html.append(_render_dark(
                slide, slide_num, total_slides, progress_pct,
                handle, brand_name, year, P, PL, img_b64,
            ))
        elif slide.theme == "light":
            if slide.type == "cta":
                slides_html.append(_render_cta(
                    slide, slide_num, total_slides, progress_pct,
                    handle, brand_name, year, P, PL, DB,
                ))
            else:
                slides_html.append(_render_light(
                    slide, slide_num, total_slides, progress_pct,
                    handle, brand_name, year, P, DB, LR, img_b64,
                ))
        elif slide.theme == "gradient":
            slides_html.append(_render_gradient(
                slide, slide_num, total_slides, progress_pct,
                handle, brand_name, year,
            ))

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{brand_name} — Carrossel</title>
<style>
{fonts_css}

:root {{
  --P: {P};
  --PL: {PL};
  --PD: {PD};
  --LB: {LB};
  --LR: {LR};
  --DB: {DB};
  --G: {G};
  --F-HEAD: '{font_headline}', sans-serif;
  --F-BODY: '{font_body}', sans-serif;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a1a; padding: 20px; font-family: var(--F-BODY); }}

/* Controls */
.controls {{
  text-align: center;
  margin-bottom: 24px;
}}
.controls button {{
  background: var(--P);
  color: #fff;
  border: none;
  padding: 12px 28px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 1px;
  text-transform: uppercase;
}}
.controls button:hover {{ opacity: 0.9; }}

/* Slides container */
.slides-wrap {{
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  justify-content: center;
  max-width: 1400px;
  margin: 0 auto;
}}
.slides-wrap.full-mode {{
  flex-direction: column;
  align-items: center;
  gap: 20px;
}}

/* Slide base */
.slide {{
  width: 1080px;
  height: 1350px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}}
.slides-wrap:not(.full-mode) .slide {{
  transform: scale(0.30);
  transform-origin: top left;
  margin-bottom: -945px;
  margin-right: -756px;
}}

/* Accent bar */
.accent-bar {{
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 7px;
  z-index: 30;
  background: var(--G);
}}
.accent-bar.on-grad {{ background: rgba(255,255,255,0.18); }}

/* Brand bar */
.brand-bar {{
  position: absolute;
  top: 7px; left: 0; right: 0;
  padding: 32px 56px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 20;
  font-family: var(--F-BODY);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}}
.brand-bar.on-light {{ color: rgba(15,13,12,0.45); }}
.brand-bar.on-dark {{ color: rgba(255,255,255,0.45); }}
.brand-bar.on-grad {{ color: rgba(255,255,255,0.50); }}

/* Progress bar */
.prog {{
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 0 56px 30px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: var(--F-BODY);
}}
.prog-track {{
  flex: 1;
  height: 3px;
  border-radius: 2px;
  overflow: hidden;
}}
.prog-fill {{ height: 100%; border-radius: 2px; }}
.prog-num {{ font-size: 15px; font-weight: 600; }}
.on-light .prog-track {{ background: rgba(0,0,0,0.08); }}
.on-light .prog-fill {{ background: var(--P); }}
.on-light .prog-num {{ color: rgba(0,0,0,0.22); }}
.on-dark .prog-track {{ background: rgba(255,255,255,0.10); }}
.on-dark .prog-fill {{ background: #fff; }}
.on-dark .prog-num {{ color: rgba(255,255,255,0.22); }}
.on-grad .prog-track {{ background: rgba(255,255,255,0.15); }}
.on-grad .prog-fill {{ background: rgba(255,255,255,0.6); }}
.on-grad .prog-num {{ color: rgba(255,255,255,0.30); }}

/* Content area */
.content {{
  position: absolute;
  top: 110px; left: 56px; right: 56px; bottom: 80px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 40px;
  z-index: 10;
}}

/* Tag */
.tag {{
  font-family: var(--F-BODY);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 24px;
}}
.on-light .tag {{ color: var(--P); }}
.on-dark .tag {{ color: var(--PL); }}
.on-grad .tag {{ color: rgba(255,255,255,0.55); }}

/* ===================== CAPA ===================== */
.slide-capa {{ background: #000; }}
.capa-bg {{
  position: absolute; inset: 0;
  background-size: cover;
  background-position: center;
}}
.capa-grad {{
  position: absolute; inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,0.35) 0%,
    rgba(0,0,0,0.08) 25%,
    rgba(0,0,0,0.15) 40%,
    rgba(0,0,0,0.65) 55%,
    rgba(0,0,0,0.92) 75%,
    rgba(0,0,0,0.99) 100%
  );
}}
.capa-headline-area {{
  position: absolute;
  bottom: 120px; left: 0; right: 0;
  padding: 0 52px;
  z-index: 10;
}}
.capa-badge {{
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(0,0,0,0.38);
  border: 1.5px solid rgba(255,255,255,0.12);
  border-radius: 60px;
  padding: 12px 26px 12px 14px;
  backdrop-filter: blur(10px);
  width: fit-content;
  margin-bottom: 32px;
}}
.badge-dot {{
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--G);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--F-BODY);
  font-size: 16px;
  font-weight: 900;
  color: #fff;
}}
.badge-handle {{
  font-family: var(--F-BODY);
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.3px;
}}
.badge-check {{
  width: 22px; height: 22px;
  background: var(--P);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.capa-headline {{
  font-family: var(--F-HEAD);
  font-size: 108px;
  font-weight: 900;
  line-height: 0.93;
  letter-spacing: -3px;
  text-transform: uppercase;
  color: #fff;
}}
.capa-headline em {{
  color: var(--P);
  font-style: normal;
}}

/* ===================== DARK ===================== */
.slide-dark {{ background: var(--DB); }}
.dark-h1 {{
  font-family: var(--F-HEAD);
  font-size: 80px;
  font-weight: 900;
  line-height: 0.97;
  letter-spacing: -2px;
  text-transform: uppercase;
  color: #fff;
  margin-bottom: 36px;
}}
.dark-h1 em {{ color: var(--P); font-style: normal; }}
.dark-bg-num {{
  position: absolute;
  right: -10px; bottom: 50px;
  font-family: var(--F-HEAD);
  font-size: 380px;
  font-weight: 900;
  color: rgba(255,255,255,0.04);
  line-height: 1;
  letter-spacing: -14px;
  pointer-events: none;
  z-index: 1;
}}
.dark-body {{
  font-family: var(--F-BODY);
  font-size: 38px;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: -0.2px;
  color: rgba(255,255,255,0.55);
}}
.dark-body strong {{ color: #fff; font-weight: 700; }}
.dark-body em {{ color: var(--PL); font-style: normal; }}
.dark-card {{
  background: rgba(255,255,255,0.04);
  border-left: 6px solid var(--P);
  border-radius: 16px;
  padding: 44px 48px;
}}
.dark-arrow-row {{
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 28px;
}}
.dark-arrow-row::before {{
  content: '→';
  font-size: 32px;
  color: rgba(255,255,255,0.3);
  flex-shrink: 0;
  margin-top: 4px;
  font-family: var(--F-BODY);
}}

/* Dark with background image */
.slide-img-bg {{
  position: absolute; inset: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
}}
.slide-img-overlay {{
  position: absolute; inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(4,4,22,0.80) 0%,
    rgba(4,4,22,0.70) 30%,
    rgba(4,4,22,0.75) 60%,
    rgba(4,4,22,0.90) 100%
  );
  z-index: 1;
}}

/* ===================== LIGHT ===================== */
.slide-light {{ background: var(--LB); }}
.light-h1 {{
  font-family: var(--F-HEAD);
  font-size: 72px;
  font-weight: 900;
  line-height: 1.0;
  letter-spacing: -1.5px;
  text-transform: uppercase;
  color: var(--DB);
  margin-bottom: 32px;
}}
.light-h1 em {{ color: var(--P); font-style: normal; }}
.light-body {{
  font-family: var(--F-BODY);
  font-size: 38px;
  font-weight: 400;
  line-height: 1.55;
  letter-spacing: -0.2px;
  color: rgba(15,13,12,0.60);
}}
.light-body strong {{ color: var(--DB); font-weight: 800; }}
.light-card {{
  background: #fff;
  border-left: 7px solid var(--P);
  border-radius: 18px;
  padding: 52px 56px;
}}
.light-pcard {{
  background: #fff;
  border-radius: 18px;
  padding: 40px 48px;
  border: 1.5px solid var(--LR);
  margin-bottom: 20px;
}}
.light-table {{ width: 100%; border-collapse: collapse; }}
.light-table th {{
  background: var(--P);
  color: #fff;
  padding: 20px 24px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  text-align: left;
  font-family: var(--F-BODY);
}}
.light-table td {{
  padding: 22px 24px;
  font-size: 26px;
  font-weight: 500;
  border-bottom: 1px solid var(--LR);
  font-family: var(--F-BODY);
}}
.light-table tr:last-child td {{ border-bottom: none; }}

/* Image box */
.img-box {{
  width: 100%;
  height: 360px;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 36px;
}}
.img-box img {{
  width: 100%; height: 100%;
  object-fit: cover;
}}
.on-dark .img-box {{ border: 1.5px solid rgba(255,255,255,0.08); }}
.on-light .img-box {{ box-shadow: 0 4px 24px rgba(0,0,0,0.06); }}

/* ===================== GRADIENT ===================== */
.slide-grad {{ background: var(--G); }}
.grad-bg-num {{
  position: absolute;
  right: -15px; bottom: 40px;
  font-family: var(--F-HEAD);
  font-size: 420px;
  font-weight: 900;
  color: rgba(255,255,255,0.06);
  line-height: 1;
  letter-spacing: -16px;
  pointer-events: none;
}}
.grad-h1 {{
  font-family: var(--F-HEAD);
  font-size: 80px;
  font-weight: 900;
  line-height: 0.97;
  letter-spacing: -2px;
  text-transform: uppercase;
  color: #fff;
  margin-bottom: 40px;
}}
.grad-body {{
  font-family: var(--F-BODY);
  font-size: 38px;
  font-weight: 400;
  line-height: 1.55;
  letter-spacing: -0.2px;
  color: rgba(255,255,255,0.65);
}}
.grad-body strong {{ color: #fff; font-weight: 700; }}
.grad-row {{
  display: flex;
  align-items: flex-start;
  gap: 22px;
  margin-bottom: 30px;
}}
.grad-arrow {{
  font-size: 34px;
  color: rgba(255,255,255,0.4);
  flex-shrink: 0;
  margin-top: 4px;
  font-family: var(--F-BODY);
}}
.grad-text {{
  font-family: var(--F-BODY);
  font-size: 32px;
  font-weight: 500;
  line-height: 1.45;
  letter-spacing: -0.2px;
  color: rgba(255,255,255,0.72);
}}
.grad-text strong {{ color: #fff; font-weight: 800; }}

/* ===================== CTA ===================== */
.slide-cta {{ background: var(--LB); }}
.cta-bridge {{
  font-family: var(--F-BODY);
  font-size: 38px;
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: -0.2px;
  color: rgba(15,13,12,0.55);
  margin-bottom: 48px;
}}
.cta-bridge strong {{ color: var(--DB); font-weight: 800; }}
.cta-headline {{
  font-family: var(--F-HEAD);
  font-size: 72px;
  font-weight: 900;
  line-height: 0.97;
  letter-spacing: -2px;
  text-transform: uppercase;
  color: var(--DB);
  margin-bottom: 40px;
}}
.cta-headline em {{ color: var(--P); font-style: normal; }}
.cta-kbox {{
  background: #fff;
  border: 3px solid rgba(247,54,0,0.15);
  border-radius: 20px;
  padding: 40px 48px;
  margin-bottom: 32px;
}}
.cta-kinstr {{
  font-family: var(--F-BODY);
  font-size: 20px;
  font-weight: 500;
  color: rgba(15,13,12,0.42);
  margin-bottom: 12px;
}}
.cta-kword {{
  font-family: var(--F-HEAD);
  font-size: 80px;
  font-weight: 900;
  color: var(--P);
  letter-spacing: -2px;
  line-height: 1;
  margin-bottom: 14px;
}}
.cta-kbenefit {{
  font-family: var(--F-BODY);
  font-size: 22px;
  font-weight: 500;
  line-height: 1.5;
  color: rgba(15,13,12,0.50);
}}
.cta-footer {{
  display: flex;
  align-items: center;
  gap: 16px;
}}
.cta-footer-dot {{
  width: 40px; height: 40px;
  border-radius: 50%;
  background: var(--G);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--F-BODY);
  font-size: 16px;
  font-weight: 900;
  color: #fff;
}}
.cta-footer-text {{
  font-family: var(--F-BODY);
  font-size: 18px;
  color: rgba(15,13,12,0.35);
}}
</style>
</head>
<body>

<div class="controls">
  <button onclick="toggleView()">Alternar Preview / Tamanho Real</button>
</div>

<div class="slides-wrap" id="slidesWrap">
{''.join(slides_html)}
</div>

<script>
function toggleView() {{
  const wrap = document.getElementById('slidesWrap');
  wrap.classList.toggle('full-mode');
}}
</script>
</body>
</html>"""

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    return html


# =====================================================================
# FONT CSS BUILDER
# =====================================================================

def _build_fonts_css(font_headline: str, font_body: str) -> str:
    """Build @font-face CSS. Try base64 embedding, fallback to system fonts."""
    css_parts = []

    # Try to embed fonts from local files
    font_map = {
        "Barlow Condensed": [
            (config.FONT_BARLOW_BLACK, "900", "normal"),
            (config.FONT_HEADLINE_ITALIC, "700", "italic"),
        ],
        "Plus Jakarta Sans": [
            (config.FONT_JAKARTA, "400", "normal"),
            (config.FONT_JAKARTA_BOLD, "700", "normal"),
        ],
    }

    for family_name, variants in font_map.items():
        for path, weight, style in variants:
            if os.path.exists(path):
                b64 = _encode_font_base64(path)
                if b64:
                    ext = Path(path).suffix.lower()
                    fmt = "woff2" if ext == ".woff2" else "truetype"
                    css_parts.append(f"""@font-face {{
  font-family: '{family_name}';
  src: url(data:font/{fmt};base64,{b64}) format('{fmt}');
  font-weight: {weight};
  font-style: {style};
  font-display: swap;
}}""")

    return "\n".join(css_parts)


# =====================================================================
# SLIDE RENDERERS
# =====================================================================

def _progress_html(slide_num: int, total: int, theme: str) -> str:
    pct = (slide_num / total) * 100
    return f"""<div class="prog">
  <div class="prog-track"><div class="prog-fill" style="width:{pct:.0f}%"></div></div>
  <div class="prog-num">{slide_num}/{total}</div>
</div>"""


def _brand_bar_html(handle: str, brand_name: str, year: int, theme: str) -> str:
    return f"""<div class="brand-bar on-{theme}">
  <span>Powered by Designer AI</span>
  <span>{handle}</span>
  <span>{year} ®</span>
</div>"""


def _render_capa(slide, num, total, pct, handle, brand_name, year, headline, cover_b64, P, PL, G):
    # Split headline into words, mark every 3rd-4th word as accent
    words = headline.upper().split()
    # Simple heuristic: accent the last 2-3 words
    accent_start = max(0, len(words) - 3)
    headline_html = " ".join(words[:accent_start])
    if accent_start < len(words):
        headline_html += " <em>" + " ".join(words[accent_start:]) + "</em>"

    initial = brand_name[0].upper() if brand_name else "B"

    bg_style = f"background-image: url('{cover_b64}');" if cover_b64 else f"background: linear-gradient(135deg, #111 0%, #333 100%);"

    return f"""<div class="slide slide-capa on-dark" id="slide-{num}">
  <div class="capa-bg" style="{bg_style}"></div>
  <div class="capa-grad"></div>
  <div class="accent-bar"></div>
  {_brand_bar_html(handle, brand_name, year, "dark")}
  <div class="capa-headline-area">
    <div class="capa-badge">
      <div class="badge-dot">{initial}</div>
      <span class="badge-handle">{handle}</span>
      <div class="badge-check">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
    </div>
    <div class="capa-headline">{headline_html}</div>
  </div>
  {_progress_html(num, total, "dark")}
</div>"""


def _render_dark(slide, num, total, pct, handle, brand_name, year, P, PL, img_b64):
    ghost = f'<div class="dark-bg-num">{num:02d}</div>'

    img_html = ""
    overlay_html = ""
    extra_class = ""
    if img_b64:
        extra_class = " with-img"
        img_html = f'<div class="slide-img-bg" style="background-image: url(\'{img_b64}\');"></div>'
        overlay_html = '<div class="slide-img-overlay"></div>'

    headline_html = ""
    if slide.headline:
        # Mark words between ** as <em>
        h = slide.headline.upper()
        headline_html = f'<div class="dark-h1">{h}</div>'

    body_html = _format_body(slide.body, "dark-body")
    body2_html = _format_body(slide.body2, "dark-body") if slide.body2 else ""

    return f"""<div class="slide slide-dark on-dark{extra_class}" id="slide-{num}">
  {img_html}
  {overlay_html}
  {ghost}
  <div class="accent-bar"></div>
  {_brand_bar_html(handle, brand_name, year, "dark")}
  <div class="content">
    <div class="tag">{slide.tag}</div>
    {headline_html}
    {body_html}
    {body2_html}
  </div>
  {_progress_html(num, total, "dark")}
</div>"""


def _render_light(slide, num, total, pct, handle, brand_name, year, P, DB, LR, img_b64):
    headline_html = ""
    if slide.headline:
        h = slide.headline.upper()
        headline_html = f'<div class="light-h1">{h}</div>'

    img_box = ""
    if img_b64:
        img_box = f'<div class="img-box"><img src="{img_b64}" alt=""></div>'

    body_html = _format_body(slide.body, "light-body")
    body2_html = _format_body(slide.body2, "light-body") if slide.body2 else ""

    return f"""<div class="slide slide-light on-light" id="slide-{num}">
  <div class="accent-bar"></div>
  {_brand_bar_html(handle, brand_name, year, "light")}
  <div class="content">
    {img_box}
    <div class="tag">{slide.tag}</div>
    {headline_html}
    {body_html}
    {body2_html}
  </div>
  {_progress_html(num, total, "light")}
</div>"""


def _render_gradient(slide, num, total, pct, handle, brand_name, year):
    ghost = f'<div class="grad-bg-num">{num:02d}</div>'

    headline_html = ""
    if slide.headline:
        headline_html = f'<div class="grad-h1">{slide.headline.upper()}</div>'

    body_html = _format_body(slide.body, "grad-body")
    body2_html = _format_body(slide.body2, "grad-body") if slide.body2 else ""

    return f"""<div class="slide slide-grad on-grad" id="slide-{num}">
  {ghost}
  <div class="accent-bar on-grad"></div>
  {_brand_bar_html(handle, brand_name, year, "grad")}
  <div class="content">
    <div class="tag">{slide.tag}</div>
    {headline_html}
    {body_html}
    {body2_html}
  </div>
  {_progress_html(num, total, "grad")}
</div>"""


def _render_cta(slide, num, total, pct, handle, brand_name, year, P, PL, DB):
    initial = brand_name[0].upper() if brand_name else "B"

    # Parse CTA components from body
    bridge = slide.body or ""
    cta_headline = slide.headline or "QUER O MANUAL COMPLETO?"
    keyword = slide.tag or "MANUAL"
    benefit = slide.body2 or "e recebe o guia direto na DM"

    return f"""<div class="slide slide-cta on-light" id="slide-{num}">
  <div class="accent-bar"></div>
  {_brand_bar_html(handle, brand_name, year, "light")}
  <div class="content">
    <div class="cta-bridge">{bridge}</div>
    <div class="cta-headline">{cta_headline.upper()}</div>
    <div class="cta-kbox">
      <div class="cta-kinstr">Comenta a palavra abaixo:</div>
      <div class="cta-kword">{keyword.upper()}</div>
      <div class="cta-kbenefit">{benefit}</div>
    </div>
    <div class="cta-footer">
      <div class="cta-footer-dot">{initial}</div>
      <span class="cta-footer-text">{handle} · Envio automático via DM</span>
    </div>
  </div>
  {_progress_html(num, total, "light")}
</div>"""


# =====================================================================
# TEXT FORMATTING HELPERS
# =====================================================================

def _format_body(text: str, css_class: str) -> str:
    """Convert markdown-like formatting to HTML."""
    if not text:
        return ""
    # Convert **bold** to <strong>
    text = _md_to_html(text)
    return f'<div class="{css_class}">{text}</div>'


def _md_to_html(text: str) -> str:
    """Convert **bold** and *italic* markdown to HTML tags."""
    import re
    # **bold** → <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # *italic* → <em>
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text
