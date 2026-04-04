"""
Phase 1 smoke-test — renders a carousel cover with hardcoded data.

Usage:
    cd "Designer "
    python setup_fonts.py          # first time only
    python tests/test_cover.py
"""
import os
import sys

# Allow running from the project root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from designer import config
from designer.visual.carousel import render_cover

# ---------------------------------------------------------------------------
# Sample data — F4 formula: Provocação Pura
# ---------------------------------------------------------------------------
HEADLINE_PART1 = "A ARMADILHA DO PERFECCIONISMO:"
HEADLINE_PART2 = "POR QUE O POST IMPERFEITO VALE MAIS DO QUE O PERFEITO QUE NUNCA SAIU."

# Free high-quality photo from Unsplash (no auth required for direct URLs)
IMAGE_URL = "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=1080&h=1350&fit=crop"

HANDLE = "@designerai"
OUTPUT = os.path.join("output", "carousels", "test_cover.png")


def test_cover_red() -> None:
    img = render_cover(
        headline_part1=HEADLINE_PART1,
        headline_part2=HEADLINE_PART2,
        handle=HANDLE,
        image_source=IMAGE_URL,
        accent_color=config.ACCENT_RED,
        powered_by="Designer AI",
        year=2026,
        output_path=OUTPUT,
    )
    assert img.size == (config.CANVAS_W, config.CANVAS_H), \
        f"Wrong size: {img.size}"
    print(f"\nPASS — image size {img.size}")


def test_cover_orange() -> None:
    out = os.path.join("output", "carousels", "test_cover_orange.png")
    render_cover(
        headline_part1="O PERSONAL TRAINER DO FUTURO:",
        headline_part2="POR QUE O PROFISSIONAL QUE ENTENDE DE CONTEÚDO VAI DOMINAR O MERCADO FITNESS.",
        handle=HANDLE,
        image_source=IMAGE_URL,
        accent_color=config.ACCENT_ORANGE,
        output_path=out,
    )
    print(f"PASS — orange variant saved to {out}")


def test_cover_yellow() -> None:
    out = os.path.join("output", "carousels", "test_cover_yellow.png")
    render_cover(
        headline_part1="Heinz lança Ketchup Zero e aposta",
        headline_part2="R$ 50 MILHÕES para liderar o mercado no Brasil.",
        handle=HANDLE,
        image_source=IMAGE_URL,
        accent_color=config.ACCENT_YELLOW,
        output_path=out,
    )
    print(f"PASS — yellow variant saved to {out}")


if __name__ == "__main__":
    print("Rendering test covers …\n")
    test_cover_red()
    test_cover_orange()
    test_cover_yellow()
    print("\nAll tests passed. Check output/carousels/")
