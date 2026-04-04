#!/usr/bin/env python3
"""
Designer AI — Gerador de posts

Uso:
    python generate.py --brand <slug> --topic "<tema>"
    python generate.py --brand force-protocol --topic "por que você não ganha músculo"
    python generate.py --list-brands
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from designer.brand.profile import BrandProfile
from designer.copy.headlines import generate as generate_copy
from designer.copy.slides import generate_slides
from designer.delivery.drive import upload_carousel
from designer.delivery.discord_preview import send_for_approval
from designer.image.unsplash import get_image_url
from designer.image.imagen import generate_image
from designer.research.trends import suggest_topics
from designer.visual.carousel import render_cover
from designer.visual.slide_renderer import render_slide

SEP  = "─" * 56
SEP2 = "═" * 56


def _h(title: str) -> None:
    print(f"\n{SEP2}\n  {title}\n{SEP2}")

def _step(label: str, value: str = "") -> None:
    tick = "✓" if value else "→"
    print(f"  {tick}  {label}", end="")
    print(f"  {value}" if value else "")

def _section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


def run(brand_slug: str, topic: str, open_after: bool = False) -> str:
    """
    Pipeline completo: brand + topic → PNG salvo em output/carousels/

    Returns
    -------
    Caminho do PNG gerado.
    """
    # ------------------------------------------------------------------
    # 1. Carrega perfil de marca
    # ------------------------------------------------------------------
    _h(f"DESIGNER AI — GERANDO POST")
    print(f"\n  Marca:  {brand_slug}")
    print(f"  Tema:   {topic}\n")

    try:
        brand = BrandProfile.load(brand_slug)
    except FileNotFoundError:
        print(f"\n  ERRO: Perfil '{brand_slug}' não encontrado.")
        print(f"  Rode primeiro: python onboard.py")
        sys.exit(1)

    print(f"{SEP}")
    _step("Perfil carregado", brand.client_name)

    # ------------------------------------------------------------------
    # 2. Gera copy (headline + legenda + hashtags)
    # ------------------------------------------------------------------
    print(f"\n  Gerando copy com Claude... ", end="", flush=True)
    copy = generate_copy(topic=topic, brand=brand)
    print("pronto\n")

    _section("COPY GERADO")
    print(f"  Fórmula:    {copy.formula}")
    print(f"\n  Headline pt1 (branco):")
    print(f"    {copy.headline_part1}")
    print(f"\n  Headline pt2 (destaque):")
    print(f"    {copy.headline_part2}")
    print(f"\n  Legenda:")
    # Mostra legenda com indent
    for line in copy.caption.split("\n"):
        print(f"    {line}")
    print(f"\n  Hashtags: {' '.join(copy.hashtags[:8])}...")
    print(f"  Query imagem: {copy.image_query}")

    # ------------------------------------------------------------------
    # 3. Gera imagem de fundo com Imagen 4
    # ------------------------------------------------------------------
    _section("IMAGEM — IMAGEN 4")
    print(f"  Query scroll-stop: {copy.image_query}")
    print(f"  Gerando imagem customizada com Imagen 4... ", end="", flush=True)
    timestamp_tmp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_image_path = os.path.join("output", "tmp", f"bg_{timestamp_tmp}.png")
    try:
        generate_image(copy.image_query, output_path=tmp_image_path)
        image_source = tmp_image_path
        print("pronto")
    except Exception as e:
        print(f"falhou ({e}) — usando Pexels como fallback")
        image_source = get_image_url(copy.image_query, topic=topic)

    # ------------------------------------------------------------------
    # 4. Renderiza capa (slide 1)
    # ------------------------------------------------------------------
    _section("RENDERIZANDO")
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", "carousels", f"{brand_slug}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    handle = brand.handle or f"@{brand_slug}"
    accent = brand.accent_rgb()

    cover_path = os.path.join(output_dir, "01_capa.png")
    print(f"  Slide 01 — Capa... ", end="", flush=True)
    render_cover(
        headline_part1=copy.headline_part1,
        headline_part2=copy.headline_part2,
        handle=handle,
        image_source=image_source,
        accent_color=accent,
        powered_by="Designer AI",
        year=datetime.now().year,
        output_path=cover_path,
    )
    print("pronto")

    # ------------------------------------------------------------------
    # 5. Gera conteúdo dos slides internos
    # ------------------------------------------------------------------
    print(f"\n  Gerando conteúdo dos slides internos... ", end="", flush=True)
    slides = generate_slides(topic=topic, brand=brand, copy=copy)
    print("pronto")

    # ------------------------------------------------------------------
    # 6. Renderiza slides 2–7
    # ------------------------------------------------------------------
    slide_paths = [cover_path]
    for slide in slides:
        slide_path = os.path.join(output_dir, f"0{slide.number}_slide.png")
        print(f"  Slide 0{slide.number} — {slide.label or slide.type}... ", end="", flush=True)
        render_slide(
            slide=slide,
            accent_color=accent,
            handle=handle,
            output_path=slide_path,
        )
        slide_paths.append(slide_path)
        print("pronto")

    # ------------------------------------------------------------------
    # 7. Salva metadados JSON
    # ------------------------------------------------------------------
    meta_path = os.path.join(output_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "brand":          brand_slug,
            "topic":          topic,
            "formula":        copy.formula,
            "headline_part1": copy.headline_part1,
            "headline_part2": copy.headline_part2,
            "caption":        copy.caption,
            "hashtags":       copy.hashtags,
            "image_query":    copy.image_query,
            "image_url":      image_source,
            "slides":         [{"number": s.number, "type": s.type, "headline": s.headline, "body": s.body} for s in slides],
            "generated_at":   timestamp,
        }, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 8. Preview e aprovação no Discord
    # ------------------------------------------------------------------
    _section("DISCORD — PREVIEW")
    cover_path = slide_paths[0] if slide_paths else None
    approved = send_for_approval(
        file_path=cover_path,
        brand_slug=brand_slug,
        topic=topic,
        caption=copy.caption,
    ) if cover_path else True

    if not approved:
        print(f"\n  Carrossel não aprovado. Arquivos salvos em: {output_dir}")
        return

    # ------------------------------------------------------------------
    # 9. Upload para Google Drive
    # ------------------------------------------------------------------
    _section("GOOGLE DRIVE")
    print(f"  Enviando {len(slide_paths)} slides + meta.json... ")
    try:
        drive_urls = upload_carousel(
            files=slide_paths + [meta_path],
            brand_slug=brand_slug,
            topic=topic,
        )
        print(f"\n  ✓ {len(drive_urls)} arquivos no Drive")
        for url in drive_urls[:3]:
            print(f"    {url}")
        if len(drive_urls) > 3:
            print(f"    ... e mais {len(drive_urls) - 3} arquivos")
    except Exception as e:
        print(f"  ⚠ Drive indisponível: {e}")
        print(f"  Arquivos salvos localmente em: {output_dir}")

    # ------------------------------------------------------------------
    # 9. Resumo final
    # ------------------------------------------------------------------
    _h("CARROSSEL GERADO COM SUCESSO")
    print(f"\n  Slides:  {output_dir}/")
    print(f"  Total:   {len(slide_paths)} slides (capa + {len(slides)} internos)")
    print(f"\n  Legenda + hashtags prontos para colar no Instagram.\n")

    if open_after:
        os.system(f'open "{output_dir}"')

    return output_dir


def suggest(brand_slug: str) -> str:
    """
    Modo interativo: pesquisa tendências e apresenta temas para escolher.
    Retorna o tema escolhido pelo usuário.
    """
    try:
        brand = BrandProfile.load(brand_slug)
    except FileNotFoundError:
        print(f"\n  ERRO: Perfil '{brand_slug}' não encontrado.")
        sys.exit(1)

    _h(f"TREND RESEARCH — {brand.client_name}")
    print(f"\n  Buscando tendências para: {brand.subniche} / {brand.niche}")
    print(f"  Fontes: Tavily (web) + Google Trends BR\n")
    print(f"  Aguarde...\n")

    suggestions = suggest_topics(brand, n=5)

    print(f"{SEP}")
    print(f"  {'#':<3} {'SCORE':<7} {'FÓRMULA':<6}  TEMA")
    print(f"{SEP}")
    for i, s in enumerate(suggestions, 1):
        bar = "▓" * (s.trend_score // 10) + "░" * (10 - s.trend_score // 10)
        print(f"  {i:<3} {bar} {s.formula:<6}  {s.topic}")
        print(f"      └─ {s.angle}")
        print()

    print(f"{SEP}")
    print(f"  Digite o número do tema ou 0 para digitar o seu próprio:")
    choice = input("  → ").strip()

    if choice == "0" or not choice.isdigit():
        topic = input("  Digite o tema: ").strip()
    else:
        idx = int(choice) - 1
        if 0 <= idx < len(suggestions):
            topic = suggestions[idx].topic
        else:
            topic = input("  Opção inválida. Digite o tema: ").strip()

    return topic


def main() -> None:
    parser = argparse.ArgumentParser(description="Designer AI — Gerador de posts")
    parser.add_argument("--brand",       metavar="SLUG",  help="Slug do perfil de marca")
    parser.add_argument("--topic",       metavar="TEMA",  help="Tema do post")
    parser.add_argument("--suggest",     action="store_true", help="Sugere temas com base em tendências")
    parser.add_argument("--open",        action="store_true", help="Abre o PNG após gerar")
    parser.add_argument("--list-brands", action="store_true", help="Lista perfis disponíveis")
    args = parser.parse_args()

    if args.list_brands:
        slugs = BrandProfile.list_saved()
        if not slugs:
            print("Nenhum perfil encontrado. Rode: python onboard.py")
        else:
            print("Perfis disponíveis:")
            for s in slugs:
                print(f"  → {s}")
        return

    if not args.brand:
        # Modo totalmente interativo: pergunta a marca
        slugs = BrandProfile.list_saved()
        if not slugs:
            print("  Nenhum perfil encontrado. Rode: python onboard.py")
            sys.exit(1)
        _h("DESIGNER AI")
        print("\n  Marcas disponíveis:")
        for i, s in enumerate(slugs, 1):
            print(f"    {i}. {s}")
        choice = input("\n  Escolha a marca (número ou slug): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(slugs):
            args.brand = slugs[int(choice) - 1]
        else:
            args.brand = choice

    # Modo suggest: pesquisa tendências e deixa usuário escolher
    topic = args.topic
    if args.suggest:
        topic = suggest(args.brand)
    elif not topic:
        # Pergunta diretamente o tema
        _h(f"DESIGNER AI — {args.brand.upper()}")
        print("\n  O que é o post de hoje?")
        print("  (ou pressione Enter para ver temas sugeridos por tendências)\n")
        topic = input("  Tema: ").strip()
        if not topic:
            topic = suggest(args.brand)

    run(
        brand_slug=args.brand,
        topic=topic,
        open_after=args.open,
    )


if __name__ == "__main__":
    main()
