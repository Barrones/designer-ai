"""
Download required fonts from Google Fonts GitHub mirror.
Run once before using the renderer:

    python setup_fonts.py
"""
import os
import sys
import urllib.request

FONTS_DIR = os.path.join("designer", "visual", "fonts")

FONTS = {
    "Anton-Regular.ttf": (
        "https://github.com/google/fonts/raw/refs/heads/main/ofl/anton/Anton-Regular.ttf"
    ),
    "BarlowCondensed-BoldItalic.ttf": (
        "https://github.com/google/fonts/raw/refs/heads/main/ofl/barlowcondensed/"
        "BarlowCondensed-BoldItalic.ttf"
    ),
    # Inter is now a variable font in Google Fonts — one file covers all weights
    "Inter-Light.ttf": (
        "https://github.com/google/fonts/raw/refs/heads/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
    ),
    "Inter-Medium.ttf": (
        "https://github.com/google/fonts/raw/refs/heads/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
    ),
}


def download_font(name: str, url: str) -> None:
    dest = os.path.join(FONTS_DIR, name)
    if os.path.exists(dest):
        print(f"  already exists — skipping {name}")
        return
    print(f"  downloading {name} …", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print("done")
    except Exception as exc:
        print(f"FAILED — {exc}")
        sys.exit(1)


def main() -> None:
    os.makedirs(FONTS_DIR, exist_ok=True)
    print(f"Fonts directory: {FONTS_DIR}\n")
    for name, url in FONTS.items():
        download_font(name, url)
    print("\nAll fonts ready.")


if __name__ == "__main__":
    main()
