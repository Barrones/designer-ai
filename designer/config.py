"""Global constants — canvas dimensions, colors, font paths."""
import os
from typing import Tuple

Color = Tuple[int, int, int]

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
CANVAS_W = 1080
CANVAS_H = 1350

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
WHITE: Color = (255, 255, 255)
BLACK: Color = (0, 0, 0)

# Accent palette (pick one per post)
ACCENT_RED: Color    = (230, 57, 70)    # #E63946
ACCENT_ORANGE: Color = (255, 107, 53)   # #FF6B35
ACCENT_YELLOW: Color = (255, 214, 0)    # #FFD600

# Header / footer gradient endpoints
GRADIENT_LEFT: Color  = (26, 26, 139)   # #1A1A8B  deep blue
GRADIENT_RIGHT: Color = (139, 0, 0)     # #8B0000  dark red

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
HEADER_H = 40          # px — top bar height
FOOTER_H = 40          # px — bottom bar height
PAD_X    = 48          # px — horizontal text margin

# Headline starts at this fraction of canvas height
HEADLINE_Y_FRAC = 0.60

# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------
OVERLAY_ALPHA_TOP    = 20    # near-transparent at the very top
OVERLAY_ALPHA_BOTTOM = 220   # near-opaque at bottom (ensures text legibility)

# ---------------------------------------------------------------------------
# Font sizes
# ---------------------------------------------------------------------------
FONT_SIZE_HEADLINE = 92     # Anton — headline part 1
FONT_SIZE_ITALIC   = 88     # BarlowCondensed BoldItalic — headline part 2
FONT_SIZE_HANDLE   = 30     # Inter Medium — @handle above headline
FONT_SIZE_UI       = 21     # Inter Light — header/footer UI text

LINE_HEIGHT_HEADLINE = 100  # px between headline lines (both parts)

# ---------------------------------------------------------------------------
# Font paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
FONTS_DIR = os.path.join(_HERE, "visual", "fonts")

FONT_HEADLINE        = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")
FONT_HEADLINE_ITALIC = os.path.join(FONTS_DIR, "BarlowCondensed-BoldItalic.ttf")
FONT_UI              = os.path.join(FONTS_DIR, "Inter-Medium.ttf")
FONT_UI_LIGHT        = os.path.join(FONTS_DIR, "Inter-Light.ttf")
