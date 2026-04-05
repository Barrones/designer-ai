"""Global constants — canvas dimensions, colors, font paths, design system."""
import os
from typing import Tuple

Color = Tuple[int, int, int]

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
CANVAS_W = 1080
CANVAS_H = 1350

# ---------------------------------------------------------------------------
# Colors — Default palette (overridden per brand)
# ---------------------------------------------------------------------------
WHITE: Color = (255, 255, 255)
BLACK: Color = (0, 0, 0)

# Accent palette (pick one per post)
ACCENT_RED: Color    = (230, 57, 70)    # #E63946
ACCENT_ORANGE: Color = (255, 107, 53)   # #FF6B35
ACCENT_YELLOW: Color = (255, 214, 0)    # #FFD600

# Header / footer gradient endpoints (legacy — kept for backward compat)
GRADIENT_LEFT: Color  = (26, 26, 139)   # #1A1A8B  deep blue
GRADIENT_RIGHT: Color = (139, 0, 0)     # #8B0000  dark red

# ---------------------------------------------------------------------------
# Designer AI Design System — Derived Color Palette
# ---------------------------------------------------------------------------
# These are derived from a single primary brand color.
# Use derive_palette() to generate all values from one hex color.

DEFAULT_BRAND_PRIMARY = "#E8421A"  # Designer AI orange-red


def hex_to_rgb(hex_color: str) -> Color:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(color: Color) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"


def mix_colors(c1: Color, c2: Color, ratio: float) -> Color:
    """Mix two colors. ratio=0 → c1, ratio=1 → c2."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))


def derive_palette(primary_hex: str) -> dict:
    """
    Derive complete Designer AI color palette from a single primary color.

    Returns dict with:
        primary, primary_light, primary_dark,
        light_bg, light_border, dark_bg,
        gradient_css (for HTML renderer)
    """
    p = hex_to_rgb(primary_hex)

    # Determine warmth (warm = red/orange/yellow dominant)
    is_warm = p[0] > p[2]  # R > B = warm

    # Primary variants
    primary_light = mix_colors(p, WHITE, 0.20)
    primary_dark = mix_colors(p, BLACK, 0.30)

    # Background colors based on temperature
    if is_warm:
        light_bg = (245, 242, 239)       # #F5F2EF warm off-white
        dark_bg = (15, 13, 12)           # #0F0D0C warm near-black
    else:
        light_bg = (240, 242, 245)       # #F0F2F5 cool off-white
        dark_bg = (12, 13, 16)           # #0C0D10 cool near-black

    # Light border = light_bg darkened 5%
    light_border = mix_colors(light_bg, BLACK, 0.05)

    return {
        "primary": p,
        "primary_hex": primary_hex,
        "primary_light": primary_light,
        "primary_light_hex": rgb_to_hex(primary_light),
        "primary_dark": primary_dark,
        "primary_dark_hex": rgb_to_hex(primary_dark),
        "light_bg": light_bg,
        "light_bg_hex": rgb_to_hex(light_bg),
        "light_border": light_border,
        "light_border_hex": rgb_to_hex(light_border),
        "dark_bg": dark_bg,
        "dark_bg_hex": rgb_to_hex(dark_bg),
        "gradient_css": f"linear-gradient(165deg, {rgb_to_hex(primary_dark)} 0%, {primary_hex} 50%, {rgb_to_hex(primary_light)} 100%)",
    }


# ---------------------------------------------------------------------------
# Niche-based default palettes
# ---------------------------------------------------------------------------
NICHE_PALETTES = {
    "marketing digital":    {"primary": "#E8421A", "font_headline": "Barlow Condensed"},
    "imobiliário":          {"primary": "#1B2A4A", "font_headline": "Montserrat"},
    "fitness":              {"primary": "#1A1A2E", "font_headline": "Inter"},
    "saúde":                {"primary": "#1A1A2E", "font_headline": "Inter"},
    "gastronomia":          {"primary": "#2C1810", "font_headline": "Playfair Display"},
    "moda":                 {"primary": "#1C1C1C", "font_headline": "Cormorant Garamond"},
    "beleza":               {"primary": "#1C1C1C", "font_headline": "Cormorant Garamond"},
    "educação":             {"primary": "#1B3A4B", "font_headline": "Source Sans Pro"},
    "tech":                 {"primary": "#0A192F", "font_headline": "Space Grotesk"},
    "saas":                 {"primary": "#0A192F", "font_headline": "Space Grotesk"},
    "advocacia":            {"primary": "#1A1A2E", "font_headline": "EB Garamond"},
    "jurídico":             {"primary": "#1A1A2E", "font_headline": "EB Garamond"},
    "contabilidade":        {"primary": "#1C2541", "font_headline": "Roboto"},
    "e-commerce":           {"primary": "#1A1A1A", "font_headline": "DM Sans"},
    "pet":                  {"primary": "#2D3436", "font_headline": "Quicksand"},
    "veterinária":          {"primary": "#2D3436", "font_headline": "Quicksand"},
}

# ---------------------------------------------------------------------------
# Font pairing by visual style
# ---------------------------------------------------------------------------
STYLE_FONTS = {
    "classico":     {"headline": "Playfair Display", "body": "DM Sans"},
    "moderno":      {"headline": "Barlow Condensed", "body": "Plus Jakarta Sans"},
    "minimalista":  {"headline": "Plus Jakarta Sans", "body": "Plus Jakarta Sans"},
    "bold":         {"headline": "Space Grotesk", "body": "Space Grotesk"},
}

# ---------------------------------------------------------------------------
# Layout — Designer AI Design System
# ---------------------------------------------------------------------------
HEADER_H = 40          # px — top bar height (legacy Pillow)
FOOTER_H = 40          # px — bottom bar height (legacy Pillow)
PAD_X    = 56          # px — horizontal safe area (updated from 48)
PAD_Y_BOTTOM = 80      # px — minimum bottom padding (above progress bar)

# Accent bar
ACCENT_BAR_H = 7       # px — gradient accent bar at top

# Brand bar
BRAND_BAR_TOP = 32     # px — top padding inside brand bar
BRAND_BAR_FONT_SIZE = 14  # px

# Progress bar
PROGRESS_BAR_H = 3     # px — track height
PROGRESS_BAR_BOTTOM = 30  # px — distance from slide bottom

# Content area
CONTENT_TOP = 110      # px — top of content area
CONTENT_BOTTOM = 80    # px — bottom padding

# Headline starts at this fraction of canvas height
HEADLINE_Y_FRAC = 0.58

# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------
OVERLAY_ALPHA_TOP    = 20    # near-transparent at the very top
OVERLAY_ALPHA_BOTTOM = 220   # near-opaque at bottom (ensures text legibility)

# ---------------------------------------------------------------------------
# Font sizes — Designer AI scale (1080×1350 native)
# ---------------------------------------------------------------------------
FONT_SIZE_HEADLINE = 92      # Anton — headline part 1 (legacy)
FONT_SIZE_ITALIC   = 88      # BarlowCondensed BoldItalic — headline part 2 (legacy)
FONT_SIZE_HANDLE   = 30      # Inter Medium — @handle above headline
FONT_SIZE_UI       = 21      # Inter Light — header/footer UI text

LINE_HEIGHT_HEADLINE = 100   # px between headline lines (both parts)

# Designer AI typography scale
FONT_SCALE = {
    "capa_headline":    {"size": 108, "weight": 900, "line_height": 0.93, "letter_spacing": -3},
    "capa_headline_min": {"size": 88, "weight": 900},  # minimum if too many lines
    "dark_headline":    {"size": 80, "weight": 900, "line_height": 0.97, "letter_spacing": -2},
    "light_headline":   {"size": 72, "weight": 900, "line_height": 1.0, "letter_spacing": -1.5},
    "grad_headline":    {"size": 80, "weight": 900, "line_height": 0.97, "letter_spacing": -2},
    "body":             {"size": 38, "weight": 400, "line_height": 1.5, "letter_spacing": -0.2},
    "body_strong":      {"size": 38, "weight": 700},
    "tag":              {"size": 13, "weight": 700, "letter_spacing": 3},
    "brand_bar":        {"size": 14, "weight": 700, "letter_spacing": 1.5},
    "progress":         {"size": 15, "weight": 600},
    "cta_bridge":       {"size": 38, "weight": 500, "line_height": 1.5},
    "cta_headline":     {"size": 72, "weight": 900, "line_height": 0.97, "letter_spacing": -2},
    "cta_keyword":      {"size": 80, "weight": 900, "letter_spacing": -2},
    "big_stat":         {"size": 200, "weight": 900, "line_height": 1, "letter_spacing": -8},
    "stat_label":       {"size": 30, "weight": 500},
    "badge_handle":     {"size": 22, "weight": 700},
}

# ---------------------------------------------------------------------------
# Slide sequence templates
# ---------------------------------------------------------------------------
SLIDE_SEQUENCES = {
    5: [
        {"type": "capa",     "theme": "capa"},
        {"type": "hook",     "theme": "dark"},
        {"type": "prova",    "theme": "light"},
        {"type": "direcao",  "theme": "dark"},
        {"type": "cta",      "theme": "light"},
    ],
    7: [
        {"type": "capa",      "theme": "capa"},
        {"type": "hook",      "theme": "dark"},
        {"type": "mecanismo", "theme": "light"},
        {"type": "prova",     "theme": "dark"},
        {"type": "expansao",  "theme": "light"},
        {"type": "direcao",   "theme": "gradient"},
        {"type": "cta",       "theme": "light"},
    ],
    9: [
        {"type": "capa",      "theme": "capa"},
        {"type": "hook",      "theme": "dark"},
        {"type": "contexto",  "theme": "light"},
        {"type": "mecanismo", "theme": "dark"},
        {"type": "prova",     "theme": "light"},
        {"type": "expansao",  "theme": "dark"},
        {"type": "aplicacao", "theme": "light"},
        {"type": "direcao",   "theme": "gradient"},
        {"type": "cta",       "theme": "light"},
    ],
    12: [
        {"type": "capa",       "theme": "capa"},
        {"type": "hook",       "theme": "dark"},
        {"type": "contexto",   "theme": "light"},
        {"type": "mecanismo",  "theme": "dark"},
        {"type": "mecanismo2", "theme": "light"},
        {"type": "prova",      "theme": "dark"},
        {"type": "dados",      "theme": "light"},
        {"type": "expansao",   "theme": "dark"},
        {"type": "caso",       "theme": "light"},
        {"type": "aplicacao",  "theme": "dark"},
        {"type": "direcao",    "theme": "gradient"},
        {"type": "cta",        "theme": "light"},
    ],
}

# ---------------------------------------------------------------------------
# Carousel types — narrative arcs
# ---------------------------------------------------------------------------
CAROUSEL_ARCS = {
    "tendencia": "Hook → Contexto → Mudança → Impacto → Ação → CTA",
    "tese":      "Crença comum → Dados que desafiam → Verdade → Novo modelo → Aplicação → CTA",
    "case":      "Resultado → Quem fez → Como → Princípio → Como replicar → CTA",
    "previsao":  "Sinais fracos → Padrão → Direção → Quem se posiciona ganha → Ações → CTA",
}

# ---------------------------------------------------------------------------
# Font paths (local TTF files for Pillow renderer)
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
FONTS_DIR = os.path.join(_HERE, "visual", "fonts")

FONT_HEADLINE        = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")
FONT_HEADLINE_ITALIC = os.path.join(FONTS_DIR, "BarlowCondensed-BoldItalic.ttf")
FONT_UI              = os.path.join(FONTS_DIR, "Inter-Medium.ttf")
FONT_UI_LIGHT        = os.path.join(FONTS_DIR, "Inter-Light.ttf")

# BarlowCondensed for Designer AI-style headlines
FONT_BARLOW_BLACK    = os.path.join(FONTS_DIR, "BarlowCondensed-Black.ttf")
FONT_BARLOW_BOLD     = os.path.join(FONTS_DIR, "BarlowCondensed-Bold.ttf")
FONT_JAKARTA         = os.path.join(FONTS_DIR, "PlusJakartaSans-Regular.ttf")
FONT_JAKARTA_BOLD    = os.path.join(FONTS_DIR, "PlusJakartaSans-Bold.ttf")

# ---------------------------------------------------------------------------
# Text color presets by theme
# ---------------------------------------------------------------------------
TEXT_COLORS = {
    "dark": {
        "body":     (255, 255, 255, 140),   # rgba(255,255,255,0.55)
        "strong":   (255, 255, 255, 255),   # #fff
        "tag":      None,                    # uses primary_light
        "headline": (255, 255, 255, 255),   # #fff
    },
    "light": {
        "body":     (15, 13, 12, 153),      # rgba(15,13,12,0.60)
        "strong":   None,                    # uses dark_bg
        "tag":      None,                    # uses primary
        "headline": None,                    # uses dark_bg
    },
    "gradient": {
        "body":     (255, 255, 255, 166),   # rgba(255,255,255,0.65)
        "strong":   (255, 255, 255, 255),   # #fff
        "tag":      (255, 255, 255, 140),   # rgba(255,255,255,0.55)
        "headline": (255, 255, 255, 255),   # #fff
    },
}
