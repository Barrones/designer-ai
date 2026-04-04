#!/usr/bin/env python3
"""
Designer AI — Gerador de Vídeo (Reels)

Uso:
    python video.py --brand <slug> --topic "<tema>" --cta "Saiba mais →"
    python video.py --brand force-protocol --topic "crédito para negativados" --cta "Solicite agora →"
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from designer.brand.profile import BrandProfile
from designer.copy.headlines import generate as generate_copy
from designer.copy.multilingual import generate_multilingual
from designer.delivery.drive import upload_carousel
from designer.delivery.discord_preview import send_for_approval
from designer.video.pexels_video import get_best_video
from designer.video.composer import render_video

SEP  = "─" * 56
SEP2 = "═" * 56

def _h(t): print(f"\n{SEP2}\n  {t}\n{SEP2}")
def _s(t): print(f"\n{SEP}\n  {t}\n{SEP}")


def run(brand_slug: str, topic: str, cta: str, duration: int = 15, open_after: bool = False, country: str = "BR") -> str:

    _h("DESIGNER AI — GERANDO VÍDEO REEL")
    print(f"\n  Marca:   {brand_slug}")
    print(f"  Tema:    {topic}")
    print(f"  CTA:     {cta}")
    print(f"  Mercado: {country}\n")

    # ------------------------------------------------------------------
    # 1. Carrega perfil de marca
    # ------------------------------------------------------------------
    try:
        brand = BrandProfile.load(brand_slug)
    except FileNotFoundError:
        print(f"  ERRO: Perfil '{brand_slug}' não encontrado. Rode: python onboard.py")
        sys.exit(1)

    print(f"{SEP}")
    print(f"  ✓  Perfil carregado  {brand.client_name}")

    # ------------------------------------------------------------------
    # 2. Gera copy (headline em 2 partes)
    # ------------------------------------------------------------------
    if country.upper() == "BR":
        print(f"\n  Gerando copy com Claude (PT-BR)... ", end="", flush=True)
        copy = generate_copy(topic=topic, brand=brand)
    else:
        print(f"\n  Gerando copy com Gemini Flash ({country})... ", end="", flush=True)
        copy = generate_multilingual(topic=topic, brand=brand, country=country)
    print("pronto\n")

    _s("COPY GERADO")
    print(f"  Fórmula:      {copy.formula}")
    print(f"  Headline pt1: {copy.headline_part1}")
    print(f"  Headline pt2: {copy.headline_part2}")
    print(f"  Query foto:   {copy.image_query}")
    print(f"  Query vídeo:  {copy.video_query}")

    # ------------------------------------------------------------------
    # 3. Busca vídeo relevante no Pexels
    # ------------------------------------------------------------------
    _s("VÍDEO DE FUNDO")
    print(f"  Buscando vídeos para: {copy.video_query}")
    print(f"  Claude escolhendo o melhor visualmente...")
    video_path = get_best_video(
        image_query=copy.video_query,
        topic=topic,
        orientation="portrait",
        min_duration=duration,
        max_duration=30,
    )
    print(f"  ✓ Vídeo selecionado: {os.path.basename(video_path)}")

    # ------------------------------------------------------------------
    # 4. Compõe o vídeo final
    # ------------------------------------------------------------------
    _s("RENDERIZANDO")
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir  = os.path.join("output", "videos", f"{brand_slug}_{timestamp}")
    output_path = os.path.join(output_dir, "reel.mp4")
    os.makedirs(output_dir, exist_ok=True)

    handle = brand.handle or f"@{brand_slug}"
    accent = brand.accent_rgb()

    print(f"  Compondo vídeo 1080×1920... ", end="", flush=True)
    render_video(
        video_path=video_path,
        headline_part1=copy.headline_part1,
        headline_part2=copy.headline_part2,
        cta=cta,
        handle=handle,
        accent_color=accent,
        output_path=output_path,
        duration=duration,
    )
    print("pronto")

    # ------------------------------------------------------------------
    # 5. Preview e aprovação no Discord
    # ------------------------------------------------------------------
    _s("DISCORD — PREVIEW")
    approved = send_for_approval(
        file_path=output_path,
        brand_slug=brand_slug,
        topic=topic,
        caption=copy.caption,
    )

    if not approved:
        print(f"\n  Conteúdo não aprovado. Arquivo salvo em: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # 6. Upload para Google Drive
    # ------------------------------------------------------------------
    _s("GOOGLE DRIVE")
    print(f"  Enviando vídeo... ", end="", flush=True)
    try:
        urls = upload_carousel(
            files=[output_path],
            brand_slug=brand_slug,
            topic=topic,
            content_type="videos",
        )
        print("pronto")
        for url in urls:
            print(f"  ✓ {url}")
    except Exception as e:
        print(f"\n  ⚠ Drive indisponível: {e}")
        print(f"  Salvo em: {output_path}")

    # ------------------------------------------------------------------
    # 6. Resumo
    # ------------------------------------------------------------------
    _h("VÍDEO GERADO COM SUCESSO")
    print(f"\n  Arquivo: {output_path}")
    print(f"  Legenda:\n")
    for line in copy.caption.split("\n"):
        print(f"    {line}")
    print(f"\n  Hashtags: {' '.join(copy.hashtags[:8])}\n")

    if open_after:
        os.system(f'open "{output_path}"')

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Designer AI — Gerador de Reels")
    parser.add_argument("--brand",    metavar="SLUG",  help="Slug do perfil de marca")
    parser.add_argument("--topic",    metavar="TEMA",  help="Tema do vídeo")
    parser.add_argument("--cta",      metavar="CTA",   help='Chamada para ação (ex: "Saiba mais →")', default="Saiba mais →")
    parser.add_argument("--duration", type=int,        help="Duração em segundos (padrão: 15)", default=15)
    parser.add_argument("--open",     action="store_true", help="Abre o vídeo após gerar")
    parser.add_argument("--country",  metavar="CC", help="Código do país (BR, IT, US, ES, DE, FR...)", default="BR")
    args = parser.parse_args()

    if not args.brand or not args.topic:
        parser.print_help()
        print("\n  Exemplos:")
        print('    python video.py --brand force-protocol --topic "crédito para negativados" --cta "Solicite agora"')
        print('    python video.py --brand nike-italia --topic "scarpe da corsa" --cta "Scopri di più" --country IT')
        sys.exit(1)

    run(
        brand_slug=args.brand,
        topic=args.topic,
        cta=args.cta,
        duration=args.duration,
        open_after=args.open,
        country=args.country,
    )


if __name__ == "__main__":
    main()
