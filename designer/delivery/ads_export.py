"""
Ads Export — prepara e exporta assets para Google Ads e Meta Ads.

Google Ads (Demand Gen / Performance Max):
  - Imagens em 3 formatos: 1200x628, 1200x1200, 960x1200
  - Headlines: máx 30 chars cada, até 15
  - Descriptions: máx 90 chars cada, até 5
  - Vídeo: nosso Reel 9:16 já está no formato certo

Meta Ads (Facebook / Instagram):
  - Imagem landscape: 1200x628
  - Imagem square: 1080x1080
  - Imagem portrait: 1080x1350 (já temos)
  - Headline: máx 40 chars
  - Primary text: máx 125 chars (recomendado)
  - Vídeo: 9:16 (já temos)

Saída: pasta {output_dir}/ads/ com:
  - google_ads/ → imagens redimensionadas + ads_copy.json
  - meta_ads/   → imagens redimensionadas + ads_copy.json
  - ads_report.md → relatório completo pronto para o cliente
"""
from __future__ import annotations

import json
import os
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


# ── Especificações das plataformas ──────────────────────────────────────────

GOOGLE_SPECS = {
    "landscape": (1200, 628),   # 16:9 — Discover, Gmail, YouTube banner
    "square":    (1200, 1200),  # 1:1  — Display, Discover
    "portrait":  (960,  1200),  # 4:5  — Discover portrait
}

META_SPECS = {
    "landscape": (1200, 628),   # 1.91:1 — Feed landscape
    "square":    (1080, 1080),  # 1:1    — Feed square, Stories preview
    "portrait":  (1080, 1350),  # 4:5    — Feed portrait (já produzimos neste formato)
}

GOOGLE_MAX = {"headline": 30, "description": 90, "business_name": 25}
META_MAX   = {"headline": 40, "primary_text": 125, "description": 30}


# ── Dataclass de resultado ──────────────────────────────────────────────────

@dataclass
class AdsPackage:
    google_ads_dir: str
    meta_ads_dir: str
    report_path: str
    google_copy: dict
    meta_copy: dict


# ── Função principal ────────────────────────────────────────────────────────

def export_ads_package(
    cover_image_path: str,
    video_path: str | None,
    copy_result,               # CopyResult do headlines.py
    brand_name: str,
    output_dir: str,
    accent_color: str = "#00D4FF",
    niche: str = "",
) -> AdsPackage:
    """
    Gera pacote completo de assets para Google Ads e Meta Ads.

    Parameters
    ----------
    cover_image_path : PNG da capa do carrossel (1080×1350)
    video_path       : MP4 do Reel (1080×1920) — opcional
    copy_result      : CopyResult com headline, caption, hashtags
    brand_name       : nome da marca para campo business_name
    output_dir       : pasta base de output (ex: output/credito-livre_20260404)
    """
    ads_dir    = os.path.join(output_dir, "ads")
    google_dir = os.path.join(ads_dir, "google_ads")
    meta_dir   = os.path.join(ads_dir, "meta_ads")
    os.makedirs(google_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    # 1. Redimensiona imagens
    _resize_for_platform(cover_image_path, google_dir, GOOGLE_SPECS, "google")
    _resize_for_platform(cover_image_path, meta_dir,   META_SPECS,   "meta")

    # 2. Copia vídeo (já está no formato certo para ambas)
    if video_path and os.path.exists(video_path):
        import shutil
        shutil.copy(video_path, os.path.join(google_dir, "video_916.mp4"))
        shutil.copy(video_path, os.path.join(meta_dir,   "video_916.mp4"))

    # 3. Gera HTML5 banners para Google Display
    try:
        from designer.delivery.html5_ads import generate_html5_pack
        html5_zips = generate_html5_pack(
            copy_result=copy_result,
            brand_name=brand_name,
            niche=niche,
            accent_color=accent_color,
            cta_text="Saiba Mais",
            output_dir=os.path.dirname(google_dir),
        )
    except Exception as e:
        html5_zips = []
        print(f"  ⚠ HTML5: {e}")

    # 4. Gera copy adaptado para cada plataforma
    google_copy = _adapt_copy_google(copy_result, brand_name)
    meta_copy   = _adapt_copy_meta(copy_result)

    with open(os.path.join(google_dir, "ads_copy.json"), "w", encoding="utf-8") as f:
        json.dump(google_copy, f, ensure_ascii=False, indent=2)

    with open(os.path.join(meta_dir, "ads_copy.json"), "w", encoding="utf-8") as f:
        json.dump(meta_copy, f, ensure_ascii=False, indent=2)

    # 4. Relatório markdown para o cliente
    report_path = os.path.join(ads_dir, "ads_report.md")
    _write_report(report_path, google_copy, meta_copy, google_dir, meta_dir, video_path)

    return AdsPackage(
        google_ads_dir=google_dir,
        meta_ads_dir=meta_dir,
        report_path=report_path,
        google_copy=google_copy,
        meta_copy=meta_copy,
    )


# ── Resize ──────────────────────────────────────────────────────────────────

def _resize_for_platform(src: str, dst_dir: str, specs: dict, prefix: str) -> None:
    """Redimensiona a imagem para todos os formatos da plataforma (cover crop)."""
    img = Image.open(src).convert("RGB")

    for name, (W, H) in specs.items():
        scale = max(W / img.width, H / img.height)
        resized = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.LANCZOS,
        )
        x = (resized.width - W) // 2
        y = (resized.height - H) // 2
        cropped = resized.crop((x, y, x + W, y + H))
        out_path = os.path.join(dst_dir, f"{prefix}_{name}_{W}x{H}.jpg")
        cropped.save(out_path, "JPEG", quality=95, optimize=True)


# ── Copy Adapters ────────────────────────────────────────────────────────────

def _adapt_copy_google(copy, brand_name: str) -> dict:
    """
    Adapta o copy para Google Ads Demand Gen / Performance Max.
    Headlines: máx 30 chars. Descriptions: máx 90 chars.
    """
    # Gera até 5 headlines a partir das partes da headline + variações
    raw_headlines = _split_into_headlines(
        copy.headline_part1 + " " + copy.headline_part2,
        max_chars=30,
        count=5,
    )

    # Descrições a partir da legenda
    raw_descriptions = _split_caption_into_descriptions(
        copy.caption, max_chars=90, count=5
    )

    return {
        "platform": "Google Ads — Demand Gen / Performance Max",
        "business_name": brand_name[:GOOGLE_MAX["business_name"]],
        "headlines": raw_headlines,          # até 15 aceitos, mín 3
        "descriptions": raw_descriptions,    # até 5
        "call_to_action": "Saiba mais",      # padrão seguro
        "compliance_note": (
            "Revise antes de subir: financeiro = Special Ad Category no Google. "
            "Evite 'garantido', 'aprovação certa', 'sem recusa'."
        ),
        "image_assets": {
            "landscape_1200x628": "google_landscape_1200x628.jpg",
            "square_1200x1200":   "google_square_1200x1200.jpg",
            "portrait_960x1200":  "google_portrait_960x1200.jpg",
        },
        "video_asset": "video_916.mp4 → faça upload no YouTube antes de vincular ao Google Ads",
    }


def _adapt_copy_meta(copy) -> dict:
    """
    Adapta o copy para Meta Ads (Facebook / Instagram).
    Headline: máx 40 chars. Primary text: máx 125 chars recomendado.
    """
    headline = _truncate(copy.headline_part1, META_MAX["headline"])

    # Primary text: 2 primeiros parágrafos da legenda
    paragraphs = [p.strip() for p in copy.caption.split("\n") if p.strip()]
    primary_text = " ".join(paragraphs[:2])[:META_MAX["primary_text"]]

    description = _truncate(copy.headline_part2, META_MAX["description"])

    return {
        "platform": "Meta Ads — Facebook / Instagram",
        "headline": headline,
        "primary_text": primary_text,
        "description": description,
        "call_to_action": "Saiba Mais",
        "hashtags": " ".join(copy.hashtags[:5]),
        "compliance_note": (
            "Produto financeiro = Special Ad Category no Meta. "
            "Ative no Gerenciador de Anúncios antes de criar a campanha. "
            "Targeting limitado: sem filtro por idade/gênero/localização específica."
        ),
        "image_assets": {
            "landscape_1200x628": "meta_landscape_1200x628.jpg",
            "square_1080x1080":   "meta_square_1080x1080.jpg",
            "portrait_1080x1350": "meta_portrait_1080x1350.jpg",
        },
        "video_asset": "video_916.mp4 → sobe direto no Gerenciador de Anúncios",
    }


# ── Report ───────────────────────────────────────────────────────────────────

def _write_report(path, google_copy, meta_copy, google_dir, meta_dir, video_path) -> None:
    lines = [
        "# Designer AI — Pacote de Anúncios",
        "",
        "---",
        "",
        "## Google Ads — Demand Gen / Performance Max",
        "",
        f"**Business name:** {google_copy['business_name']}",
        "",
        "### Headlines (máx 30 chars cada)",
    ]
    for i, h in enumerate(google_copy["headlines"], 1):
        lines.append(f"{i}. {h} `({len(h)} chars)`")

    lines += [
        "",
        "### Descriptions (máx 90 chars cada)",
    ]
    for i, d in enumerate(google_copy["descriptions"], 1):
        lines.append(f"{i}. {d} `({len(d)} chars)`")

    lines += [
        "",
        f"**CTA:** {google_copy['call_to_action']}",
        "",
        "### Assets de Imagem",
        f"- Landscape 1200×628: `{google_dir}/google_landscape_1200x628.jpg`",
        f"- Square 1200×1200:   `{google_dir}/google_square_1200x1200.jpg`",
        f"- Portrait 960×1200:  `{google_dir}/google_portrait_960x1200.jpg`",
    ]

    if video_path:
        lines += [
            "",
            "### Vídeo",
            "1. Faça upload do `video_916.mp4` no YouTube (pode ser não listado)",
            "2. Copie o ID do vídeo (youtube.com/watch?v=**ESTE_ID**)",
            "3. Vincule ao asset group no Google Ads",
        ]

    lines += [
        "",
        f"> ⚠️ **Compliance:** {google_copy['compliance_note']}",
        "",
        "---",
        "",
        "## Meta Ads — Facebook / Instagram",
        "",
        f"**Headline:** {meta_copy['headline']} `({len(meta_copy['headline'])} chars)`",
        "",
        f"**Primary Text:**",
        f"> {meta_copy['primary_text']}",
        "",
        f"**Description:** {meta_copy['description']}",
        f"**CTA:** {meta_copy['call_to_action']}",
        f"**Hashtags:** {meta_copy['hashtags']}",
        "",
        "### Assets de Imagem",
        f"- Landscape 1200×628: `{meta_dir}/meta_landscape_1200x628.jpg`",
        f"- Square 1080×1080:   `{meta_dir}/meta_square_1080x1080.jpg`",
        f"- Portrait 1080×1350: `{meta_dir}/meta_portrait_1080x1350.jpg`",
    ]

    if video_path:
        lines += ["", "### Vídeo", "- `video_916.mp4` → sobe direto no Gerenciador de Anúncios"]

    lines += [
        "",
        f"> ⚠️ **Compliance:** {meta_copy['compliance_note']}",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Helpers de texto ─────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1].rstrip() + "…"


def _split_into_headlines(full_text: str, max_chars: int, count: int) -> list[str]:
    """Quebra o texto em headlines curtas respeitando o limite de chars."""
    words = full_text.upper().split()
    headlines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                headlines.append(current)
            current = word[:max_chars]
        if len(headlines) >= count:
            break
    if current and len(headlines) < count:
        headlines.append(current[:max_chars])
    return headlines[:count]


def _split_caption_into_descriptions(caption: str, max_chars: int, count: int) -> list[str]:
    """Extrai descrições dos parágrafos da legenda."""
    paragraphs = [p.strip() for p in caption.split("\n") if p.strip()]
    descriptions = []
    for p in paragraphs:
        if len(p) <= max_chars:
            descriptions.append(p)
        else:
            # Quebra em frases
            sentences = re.split(r'(?<=[.!?])\s+', p)
            chunk = ""
            for s in sentences:
                candidate = (chunk + " " + s).strip()
                if len(candidate) <= max_chars:
                    chunk = candidate
                else:
                    if chunk:
                        descriptions.append(chunk)
                    chunk = s[:max_chars]
            if chunk:
                descriptions.append(chunk[:max_chars])
        if len(descriptions) >= count:
            break
    return [d for d in descriptions if d][:count]
