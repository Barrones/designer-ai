#!/usr/bin/env python3
"""
Designer AI — Gerador de Google Display Ads (HTML5)

CLI interativo: você traz os textos, CTA, idioma e formatos.
Gera ZIPs prontos para upload no Google Ads / DV360.

Uso interativo:
    python generate_ads.py

Uso direto (sem interação):
    python generate_ads.py \
        --headline1 "Libere seu Crédito" \
        --headline2 "Sem Burocracia" \
        --cta "Saiba Mais" \
        --brand "Crédito Livre" \
        --color "#00D4FF" \
        --niche "crédito" \
        --lang pt \
        --sizes rectangle,leaderboard,half_page

    python generate_ads.py --headline1 "Shop Now" --headline2 "50% Off" \
        --cta "Buy Now" --brand "My Store" --color "#FF6600" \
        --niche "fashion" --lang en --all-sizes
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from designer.delivery.html5_ads import (
    SIZES,
    DEFAULT_SIZES,
    LANG_STRINGS,
    generate_html5_pack,
    generate_all_sizes,
)

SEP  = "─" * 60
SEP2 = "═" * 60
BOLD = "\033[1m"
DIM  = "\033[2m"
RST  = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN  = "\033[96m"


def _h(title: str) -> None:
    print(f"\n{SEP2}\n  {BOLD}{title}{RST}\n{SEP2}")


def _ok(msg: str) -> None:
    print(f"  {GREEN}✓{RST}  {msg}")


@dataclass
class AdCopy:
    headline_part1: str
    headline_part2: str
    caption: str = ""


def _ask(prompt: str, default: str = "") -> str:
    """Pergunta com default."""
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val if val else default


def _ask_choice(prompt: str, options: dict[str, str], default: str = "") -> str:
    """Pergunta com opções numeradas."""
    print(f"\n  {BOLD}{prompt}{RST}")
    keys = list(options.keys())
    for i, (k, desc) in enumerate(options.items(), 1):
        marker = f" {CYAN}← padrão{RST}" if k == default else ""
        print(f"    {i}. {k} — {desc}{marker}")
    choice = input(f"\n  Escolha (1-{len(keys)}) [{default}]: ").strip()
    if not choice:
        return default
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except ValueError:
        if choice in keys:
            return choice
    return default


def _ask_sizes() -> list[str] | None:
    """Seleção interativa de formatos."""
    print(f"\n  {BOLD}FORMATOS DISPONÍVEIS{RST}")
    print(f"  {'#':<3} {'Nome':<20} {'Dimensão':<12} {'Padrão?':<8}")
    print(f"  {SEP}")

    keys = list(SIZES.keys())
    for i, (name, (w, h)) in enumerate(SIZES.items(), 1):
        default_marker = f"{GREEN}✓{RST}" if name in DEFAULT_SIZES else " "
        print(f"  {i:<3} {name:<20} {w}x{h:<10} {default_marker}")

    print(f"\n  Opções:")
    print(f"    {CYAN}Enter{RST}    → 6 formatos padrão (✓)")
    print(f"    {CYAN}all{RST}      → todos os 14 formatos")
    print(f"    {CYAN}1,3,5{RST}    → escolher por número")
    print(f"    {CYAN}nome{RST}     → escolher por nome (ex: rectangle,leaderboard)")

    choice = input(f"\n  Formatos: ").strip()

    if not choice:
        return None  # usa DEFAULT_SIZES

    if choice.lower() == "all":
        return list(SIZES.keys())

    parts = [p.strip() for p in choice.split(",")]

    # Se são números
    if all(p.isdigit() for p in parts):
        selected = []
        for p in parts:
            idx = int(p) - 1
            if 0 <= idx < len(keys):
                selected.append(keys[idx])
        return selected if selected else None

    # Se são nomes
    selected = [p for p in parts if p in SIZES]
    return selected if selected else None


def interactive_mode() -> dict:
    """Coleta inputs do usuário interativamente."""
    _h("DESIGNER AI — GOOGLE DISPLAY ADS")
    print(f"  Preencha os dados do seu anúncio.\n")

    # Textos
    print(f"  {BOLD}TEXTOS{RST}")
    headline1 = _ask("Headline 1 (atenção)", "")
    while not headline1:
        print(f"    {YELLOW}⚠ Headline 1 é obrigatório{RST}")
        headline1 = _ask("Headline 1 (atenção)", "")

    headline2 = _ask("Headline 2 (benefício)", "")
    while not headline2:
        print(f"    {YELLOW}⚠ Headline 2 é obrigatório{RST}")
        headline2 = _ask("Headline 2 (benefício)", "")

    cta_text = _ask("CTA (botão)", "Saiba Mais")
    brand_name = _ask("Nome da marca", "")

    # Idioma
    lang = _ask_choice(
        "IDIOMA",
        {
            "pt": "Português (Brasil)",
            "en": "English",
            "es": "Español",
        },
        default="pt",
    )

    # Cor
    print()
    accent_color = _ask("Cor de destaque (hex)", "#00D4FF")
    if not accent_color.startswith("#"):
        accent_color = f"#{accent_color}"

    # Nicho
    niche = _ask_choice(
        "NICHO (define efeitos visuais)",
        {
            "finance":   "Loading bar, análise de perfil",
            "tech":      "Typing effect, estilo código",
            "ecommerce": "Badge de desconto, shine",
            "premium":   "Reveal elegante, linhas",
            "default":   "Prova social, fade simples",
        },
        default="default",
    )

    # Formatos
    sizes = _ask_sizes()

    # Output
    print()
    output_dir = _ask("Pasta de saída", f"output/ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    return {
        "headline1": headline1,
        "headline2": headline2,
        "cta_text": cta_text,
        "brand_name": brand_name,
        "lang": lang,
        "accent_color": accent_color,
        "niche": niche,
        "sizes": sizes,
        "output_dir": output_dir,
    }


def generate(params: dict) -> list[str]:
    """Executa a geração com os parâmetros fornecidos."""
    copy = AdCopy(
        headline_part1=params["headline1"],
        headline_part2=params["headline2"],
    )

    _h("GERANDO HTML5 BANNERS")
    print(f"  Headline 1:  {params['headline1']}")
    print(f"  Headline 2:  {params['headline2']}")
    print(f"  CTA:         {params['cta_text']}")
    print(f"  Marca:       {params['brand_name'] or '(sem marca)'}")
    print(f"  Idioma:      {params['lang']}")
    print(f"  Cor:         {params['accent_color']}")
    print(f"  Nicho:       {params['niche']}")

    sizes = params.get("sizes")
    if sizes:
        print(f"  Formatos:    {len(sizes)} selecionados")
    else:
        print(f"  Formatos:    6 padrão")

    print(f"\n  Gerando...\n")

    zips = generate_html5_pack(
        copy_result=copy,
        brand_name=params["brand_name"],
        niche=params["niche"],
        accent_color=params["accent_color"],
        cta_text=params["cta_text"],
        output_dir=params["output_dir"],
        sizes=sizes,
        lang=params["lang"],
    )

    # Resumo
    ads_dir = os.path.join(params["output_dir"], "ads", "google_display")
    _h("PRONTO!")
    print(f"\n  Pasta:     {ads_dir}/")
    print(f"  Banners:   {len(zips)} ZIPs gerados")
    print(f"\n  {BOLD}Para subir no Google Ads / DV360:{RST}")
    print(f"    1. Abra Google Ads → Nova campanha → Display")
    print(f"    2. Upload ad → selecione o .zip")
    print(f"    3. O Google injeta o clickTag automaticamente")
    print(f"\n  {DIM}Cada ZIP contém: index.html + style.css + script.js{RST}")
    print()

    return zips


def main():
    parser = argparse.ArgumentParser(
        description="Designer AI — Gerador de Google Display Ads (HTML5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--headline1", help="Headline parte 1 (atenção)")
    parser.add_argument("--headline2", help="Headline parte 2 (benefício)")
    parser.add_argument("--cta", default="Saiba Mais", help="Texto do CTA (botão)")
    parser.add_argument("--brand", default="", help="Nome da marca")
    parser.add_argument("--color", default="#00D4FF", help="Cor de destaque (hex)")
    parser.add_argument("--niche", default="default", help="Nicho: finance, tech, ecommerce, premium, default")
    parser.add_argument("--lang", default="pt", choices=["pt", "en", "es"], help="Idioma")
    parser.add_argument("--sizes", default="", help="Formatos (ex: rectangle,leaderboard,half_page)")
    parser.add_argument("--all-sizes", action="store_true", help="Gerar todos os 14 formatos")
    parser.add_argument("--output", default="", help="Pasta de saída")
    parser.add_argument("--list-sizes", action="store_true", help="Listar formatos disponíveis e sair")

    args = parser.parse_args()

    # Lista formatos
    if args.list_sizes:
        print(f"\n  {'Nome':<20} {'Dimensão':<12} {'Padrão?'}")
        print(f"  {SEP}")
        for name, (w, h) in SIZES.items():
            d = "✓" if name in DEFAULT_SIZES else ""
            print(f"  {name:<20} {w}x{h:<10} {d}")
        print()
        return

    # Modo direto (com argumentos)
    if args.headline1 and args.headline2:
        sizes = None
        if args.all_sizes:
            sizes = list(SIZES.keys())
        elif args.sizes:
            sizes = [s.strip() for s in args.sizes.split(",") if s.strip() in SIZES]

        params = {
            "headline1": args.headline1,
            "headline2": args.headline2,
            "cta_text": args.cta,
            "brand_name": args.brand,
            "accent_color": args.color if args.color.startswith("#") else f"#{args.color}",
            "niche": args.niche,
            "lang": args.lang,
            "sizes": sizes,
            "output_dir": args.output or f"output/ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }
        generate(params)
        return

    # Modo interativo
    params = interactive_mode()
    generate(params)


if __name__ == "__main__":
    main()
