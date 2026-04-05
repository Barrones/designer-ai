#!/usr/bin/env python3
"""
Designer AI — Gerador de Carrosséis v5

Pipeline completo:
  1. Carrega marca
  2. Gera 10 headlines → usuário escolhe
  3. Gera espinha dorsal
  4. Gera slides (alternado dark/light)
  5. Validação editorial anti-AI slop
  6. Renderiza HTML + PNGs

Uso:
    python generate_carousel.py --brand <slug> --topic "<tema>"
    python generate_carousel.py --brand <slug> --topic "<tema>" --slides 9
    python generate_carousel.py --brand <slug> --topic "<tema>" --type tendencia
    python generate_carousel.py --brand <slug> --topic "<tema>" --auto
    python generate_carousel.py --list-brands
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
from designer.copy.headlines import generate_headlines, generate as generate_copy
from designer.copy.slides import generate_carousel_slides, SlideContent
from designer.copy.editorial_filter import quick_scan, validate_and_fix
from designer.visual.carousel import render_cover
from designer.visual.slide_renderer import render_slide
from designer.visual.html_renderer import render_html
from designer.image.unsplash import get_image_url
from designer.delivery.figma_export import format_for_figma, print_figma_output
from designer import config

SEP  = "─" * 60
SEP2 = "═" * 60
BOLD = "\033[1m"
DIM  = "\033[2m"
RST  = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED   = "\033[91m"
CYAN  = "\033[96m"


def _h(title: str) -> None:
    print(f"\n{SEP2}\n  {BOLD}{title}{RST}\n{SEP2}")


def _ok(msg: str) -> None:
    print(f"  {GREEN}✓{RST}  {msg}")


def _warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RST}  {msg}")


def _err(msg: str) -> None:
    print(f"  {RED}✗{RST}  {msg}")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

def run(
    brand_slug: str,
    topic: str,
    n_slides: int = 9,
    carousel_type: str = "tendencia",
    cta_text: str = "",
    auto_mode: bool = False,
    cover_image: str = "",
    open_after: bool = False,
) -> str:
    """
    Pipeline completo: brand + topic → HTML + PNGs

    Parameters
    ----------
    brand_slug     : slug do perfil de marca
    topic          : tema do carrossel
    n_slides       : 5, 7, 9 ou 12
    carousel_type  : tendencia | tese | case | previsao
    cta_text       : texto do CTA (ex: "Comenta GUIA")
    auto_mode      : True = pula interação, escolhe headline #1
    cover_image    : caminho para imagem de capa (opcional)
    open_after     : True = abre pasta após gerar
    """

    # ------------------------------------------------------------------
    # 1. CARREGA MARCA
    # ------------------------------------------------------------------
    _h("DESIGNER AI — CARROSSEL v5")
    print(f"\n  Marca:    {brand_slug}")
    print(f"  Tema:     {topic}")
    print(f"  Slides:   {n_slides}")
    print(f"  Tipo:     {carousel_type}\n")

    try:
        brand = BrandProfile.load(brand_slug)
    except FileNotFoundError:
        _err(f"Perfil '{brand_slug}' não encontrado. Rode: python onboard.py")
        sys.exit(1)

    _ok(f"Marca carregada: {brand.client_name}")

    # Gera paleta de cores
    palette = brand.designer_palette()
    accent = brand.accent_rgb()
    handle = brand.handle or f"@{brand_slug}"
    _ok(f"Paleta derivada: {palette['primary_hex']}")

    # ------------------------------------------------------------------
    # 2. GERA 10 HEADLINES
    # ------------------------------------------------------------------
    _h("ETAPA 1 — HEADLINES")
    print(f"  Gerando 10 headlines calibradas... ", end="", flush=True)
    hl_result = generate_headlines(topic=topic, brand=brand)
    print("pronto\n")

    print(f"  {DIM}Triagem:{RST} {hl_result.triagem}")
    print(f"  {DIM}Eixo:{RST} {hl_result.eixo} · {DIM}Funil:{RST} {hl_result.funil}\n")

    print(f"  {'#':<3} {'Formato':<4}  {'Gatilhos':<30} Headline")
    print(f"  {SEP}")
    for h in hl_result.headlines:
        fmt = h.format_type
        triggers = " · ".join(h.triggers[:2]) if h.triggers else "—"
        # Trunca headline para caber no terminal
        hl_display = h.headline[:80] + "..." if len(h.headline) > 80 else h.headline
        print(f"  {h.number:<3} {fmt:<4}  {triggers:<30} {hl_display}")
    print()

    # Escolhe headline
    if auto_mode:
        chosen_idx = 0
        print(f"  {CYAN}→ Modo auto: headline #1 selecionada{RST}\n")
    else:
        print(f"  Escolha 1-10 (ou 'r' para refazer): ", end="")
        choice = input().strip()
        if choice.lower() == "r":
            print(f"\n  Refazendo headlines...\n")
            return run(brand_slug, topic, n_slides, carousel_type, cta_text, auto_mode, cover_image, open_after)
        try:
            chosen_idx = int(choice) - 1
            if not (0 <= chosen_idx < len(hl_result.headlines)):
                chosen_idx = 0
        except ValueError:
            chosen_idx = 0

    headline = hl_result.headlines[chosen_idx].headline
    _ok(f"Headline escolhida: {headline[:70]}...")

    # ------------------------------------------------------------------
    # 3. GERA SLIDES
    # ------------------------------------------------------------------
    _h("ETAPA 2 — SLIDES")
    print(f"  Gerando {n_slides} slides ({carousel_type})... ", end="", flush=True)

    slides = generate_carousel_slides(
        topic=topic,
        brand=brand,
        headline=headline,
        n_slides=n_slides,
        carousel_type=carousel_type,
        cta_text=cta_text or "Comenta a palavra-chave",
    )
    print("pronto\n")

    # Mostra preview dos slides
    for s in slides:
        theme_icon = {"capa": "🖼", "dark": "⬛", "light": "⬜", "gradient": "🟧"}.get(s.theme, "·")
        tag_display = f" [{s.tag}]" if s.tag else ""
        hl_display = f" — {s.headline[:50]}" if s.headline else ""
        print(f"  {theme_icon} Slide {s.number:>2} ({s.type:<10} {s.theme:<8}){tag_display}{hl_display}")
    print()

    # ------------------------------------------------------------------
    # 4. VALIDAÇÃO EDITORIAL
    # ------------------------------------------------------------------
    _h("ETAPA 3 — VALIDAÇÃO EDITORIAL")
    print(f"  Verificando anti-AI slop... ", end="", flush=True)

    all_texts = []
    for s in slides:
        if s.body:
            all_texts.append(s.body)
        if s.body2:
            all_texts.append(s.body2)

    quick_issues = quick_scan(all_texts)
    print("pronto\n")

    if quick_issues:
        _warn(f"{len(quick_issues)} problemas encontrados no scan rápido:")
        for issue in quick_issues[:5]:
            print(f"    [{issue.parameter}] {issue.description} ({issue.location})")
        if len(quick_issues) > 5:
            print(f"    ... e mais {len(quick_issues) - 5}")

        if not auto_mode:
            print(f"\n  Corrigir automaticamente? (s/n): ", end="")
            fix = input().strip().lower()
        else:
            fix = "s"

        if fix == "s":
            print(f"  Corrigindo com Claude... ", end="", flush=True)
            fixed_texts, result = validate_and_fix(all_texts, headline, max_retries=1)
            print("pronto")
            _ok(f"Aprovado: {result.approved} | Issues restantes: {result.total_issues}")

            # Aplica textos corrigidos de volta nos slides
            text_idx = 0
            for s in slides:
                if s.body and text_idx < len(fixed_texts):
                    s.body = fixed_texts[text_idx]
                    text_idx += 1
                if s.body2 and text_idx < len(fixed_texts):
                    s.body2 = fixed_texts[text_idx]
                    text_idx += 1
    else:
        _ok("Nenhum problema de AI slop detectado")

    # ------------------------------------------------------------------
    # 5. IMAGEM DE CAPA
    # ------------------------------------------------------------------
    _h("ETAPA 4 — IMAGEM")

    if cover_image and os.path.exists(cover_image):
        image_source = cover_image
        _ok(f"Imagem de capa: {cover_image}")
    else:
        print(f"  Buscando imagem de capa... ", end="", flush=True)
        try:
            image_source = get_image_url(topic, topic=topic)
            print("pronto")
            _ok(f"Imagem: {image_source[:60]}...")
        except Exception as e:
            image_source = ""
            _warn(f"Sem imagem disponível ({e}). Usando fundo sólido.")

    # ------------------------------------------------------------------
    # 6. RENDERIZA HTML
    # ------------------------------------------------------------------
    _h("ETAPA 5 — RENDER")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", "carousels", f"{brand_slug}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    # HTML
    html_path = os.path.join(output_dir, "carousel.html")
    print(f"  Gerando HTML... ", end="", flush=True)

    font_headline = brand.typography.headline if hasattr(brand.typography, 'headline') else "Barlow Condensed"
    font_body = brand.typography.body if hasattr(brand.typography, 'body') else "Plus Jakarta Sans"

    html = render_html(
        slides=slides,
        brand_name=brand.client_name,
        handle=handle,
        palette=palette,
        headline=headline,
        cover_image=image_source if image_source and os.path.exists(image_source) else None,
        font_headline=font_headline,
        font_body=font_body,
        year=datetime.now().year,
        output_path=html_path,
    )
    print("pronto")
    _ok(f"HTML: {html_path}")

    # PNGs (Pillow)
    print(f"\n  Renderizando PNGs com Pillow...")

    # Capa
    cover_path = os.path.join(output_dir, "01_capa.png")
    print(f"    Slide 01 — Capa... ", end="", flush=True)
    try:
        render_cover(
            headline_part1=headline.split(":")[0].strip() if ":" in headline else headline,
            headline_part2=headline.split(":")[-1].strip() if ":" in headline else "",
            handle=handle,
            image_source=image_source if image_source else "gradient",
            accent_color=accent,
            powered_by="Designer AI",
            year=datetime.now().year,
            output_path=cover_path,
        )
        print("pronto")
    except Exception as e:
        print(f"falhou ({e})")
        cover_path = None

    # Slides internos
    slide_paths = [cover_path] if cover_path else []
    for s in slides:
        if s.type == "capa":
            continue
        slide_path = os.path.join(output_dir, f"{s.number:02d}_{s.type}.png")
        print(f"    Slide {s.number:02d} — {s.type} ({s.theme})... ", end="", flush=True)
        try:
            render_slide(
                slide=s,
                accent_color=accent,
                handle=handle,
                palette=palette,
                total_slides=n_slides,
                brand_name=brand.client_name,
                year=datetime.now().year,
                output_path=slide_path,
            )
            slide_paths.append(slide_path)
            print("pronto")
        except Exception as e:
            print(f"falhou ({e})")

    # ------------------------------------------------------------------
    # 7. LEGENDA
    # ------------------------------------------------------------------
    _h("ETAPA 6 — LEGENDA")
    print(f"  Gerando copy completo... ", end="", flush=True)
    copy = generate_copy(topic=topic, brand=brand)
    print("pronto\n")

    print(f"  {DIM}Legenda:{RST}")
    for line in copy.caption.split("\n"):
        print(f"    {line}")
    print(f"\n  {DIM}Hashtags:{RST} {' '.join(copy.hashtags[:10])}")

    # ------------------------------------------------------------------
    # 8. SALVA METADADOS
    # ------------------------------------------------------------------
    meta = {
        "brand": brand_slug,
        "topic": topic,
        "headline": headline,
        "triagem": hl_result.triagem,
        "eixo": hl_result.eixo,
        "funil": hl_result.funil,
        "carousel_type": carousel_type,
        "n_slides": n_slides,
        "slides": [
            {
                "number": s.number,
                "type": s.type,
                "theme": s.theme,
                "tag": s.tag,
                "headline": s.headline,
                "body": s.body,
                "body2": s.body2,
            }
            for s in slides
        ],
        "caption": copy.caption,
        "hashtags": copy.hashtags,
        "palette": {
            "primary": palette["primary_hex"],
            "light": palette["primary_light_hex"],
            "dark": palette["primary_dark_hex"],
        },
        "generated_at": timestamp,
    }

    meta_path = os.path.join(output_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 9. EXPORTAÇÃO FIGMA
    # ------------------------------------------------------------------
    _h("ETAPA 7 — FIGMA")
    print(f"  Gerando output para plugin Figma... ", end="", flush=True)
    figma_payload = format_for_figma(
        slides=slides,
        palette=palette,
        handle=handle,
        brand_name=brand.client_name,
    )
    figma_output = print_figma_output(figma_payload)
    figma_path = os.path.join(output_dir, "figma.txt")
    with open(figma_path, "w", encoding="utf-8") as f:
        f.write(figma_output)
    print("pronto")
    _ok(f"Figma: {figma_path}")

    # ------------------------------------------------------------------
    # 10. GOOGLE DISPLAY ADS (HTML5)
    # ------------------------------------------------------------------
    _h("ETAPA 8 — GOOGLE DISPLAY ADS")
    print(f"  Gerando banners HTML5... ", end="", flush=True)
    try:
        from designer.delivery.html5_ads import generate_html5_pack
        html5_zips = generate_html5_pack(
            copy_result=copy,
            brand_name=brand.client_name,
            niche=brand.niche if hasattr(brand, 'niche') else topic,
            accent_color=palette["primary_hex"],
            cta_text=cta_text or "Saiba Mais",
            output_dir=output_dir,
        )
        print("pronto")
        _ok(f"HTML5 Ads: {len(html5_zips)} banners em {output_dir}/ads/google_display/")
    except Exception as e:
        html5_zips = []
        print("falhou")
        _warn(f"HTML5 Ads: {e}")

    # ------------------------------------------------------------------
    # 11. RESUMO
    # ------------------------------------------------------------------
    _h("CARROSSEL GERADO")
    print(f"\n  Pasta:      {output_dir}/")
    print(f"  HTML:       carousel.html {DIM}(abrir no browser para preview){RST}")
    print(f"  PNGs:       {len(slide_paths)} slides")
    print(f"  Figma:      figma.txt {DIM}(copiar e colar no plugin Figma){RST}")
    if html5_zips:
        print(f"  HTML5 Ads:  {len(html5_zips)} banners {DIM}(ads/google_display/*.zip){RST}")
    print(f"  Metadados:  meta.json")
    print(f"  Headline:   {headline[:60]}...")
    print(f"  Tipo:       {carousel_type} · {n_slides} slides")
    print()

    # ------------------------------------------------------------------
    # 10. CHECKLIST DE PUBLICAÇÃO
    # ------------------------------------------------------------------
    _h("CHECKLIST — ANTES DE PUBLICAR")
    checklist = [
        ("CONTEÚDO", [
            "O hook de capa faria VOCÊ parar o scroll?",
            "Tem pelo menos 2 dados com fonte nomeada?",
            "O conteúdo é 100% educativo (zero venda direta)?",
            "Quem compartilhar parece bem informado?",
            "Os títulos internos são concretos (não genéricos)?",
        ]),
        ("DESIGN", [
            "As cores são da SUA marca?",
            "A tipografia está legível no celular?",
            "A alternância escuro/claro está fluindo?",
            "Nenhum texto cortado ou sobrepondo a progress bar?",
        ]),
        ("PUBLICAÇÃO", [
            "O CTA do último slide está claro?",
            "A legenda tem gancho forte (primeiras 125 chars)?",
            "Hashtags relevantes (5-12)?",
        ]),
    ]
    for section, items in checklist:
        print(f"\n  {BOLD}{section}{RST}")
        for item in items:
            print(f"    {DIM}☐{RST}  {item}")
    print()

    if open_after:
        os.system(f'open "{output_dir}"')

    return output_dir


# ============================================================
# PROMPTS PRONTOS — templates para qualquer nicho
# ============================================================

PROMPT_TEMPLATES = [
    ("Tendência quente", "Pesquise a tendência mais quente de {nicho} dessa semana e crie um carrossel completo"),
    ("Tese contraintuitiva", "Por que a estratégia que todo mundo de {nicho} está usando pode estar errada"),
    ("IA no nicho", "Como a IA está mudando {nicho} — com dados reais e fontes"),
    ("Case de sucesso", "Como [marca referência] de {nicho} conseguiu [resultado]. O que podemos replicar"),
    ("Previsão", "3 sinais de que {nicho} vai mudar nos próximos 12 meses"),
    ("Dado surpreendente", "O dado mais surpreendente de {nicho} que saiu recentemente"),
    ("Antes vs Agora", "Como era {nicho} há 5 anos vs como é hoje — com dados"),
    ("Internacional vs Brasil", "Algo que {nicho} internacional já faz mas o Brasil ainda não"),
    ("Comportamento inesperado", "Por que os profissionais mais bem pagos de {nicho} estão fazendo [comportamento inesperado]"),
    ("A morte de...", "A morte de [prática antiga de {nicho}] e o que está substituindo"),
]

EDITORIAL_CALENDAR = {
    0: ("Tendência Interpretada", "tendencia", "Notícias frescas do fim de semana"),  # segunda
    1: ("Tese Contraintuitiva", "tese", "Desafiar crenças gera debate"),              # terça
    2: ("Case / Benchmark", "case", "Cases concretos como prova"),                     # quarta
    3: ("Previsão / Futuro", "previsao", "Visão de futuro pro público"),               # quinta
    4: ("Tendência (outro tema)", "tendencia", "Conteúdo compartilhável pro fim de semana"),  # sexta
}


def show_prompt_templates(nicho: str) -> str:
    """Mostra os 10 prompts prontos e retorna o escolhido."""
    _h("PROMPTS PRONTOS")
    print(f"  Substitua os placeholders pelo seu contexto.\n")
    for i, (name, template) in enumerate(PROMPT_TEMPLATES, 1):
        topic = template.format(nicho=nicho)
        print(f"  {CYAN}{i:>2}.{RST} {BOLD}{name}{RST}")
        print(f"      {DIM}{topic}{RST}")
    print(f"\n  {CYAN} 0.{RST} Digitar meu próprio tema\n")

    choice = input("  Escolha (0-10): ").strip()
    if choice == "0" or not choice.isdigit():
        return input("  Digite o tema: ").strip()

    idx = int(choice) - 1
    if 0 <= idx < len(PROMPT_TEMPLATES):
        topic = PROMPT_TEMPLATES[idx][1].format(nicho=nicho)
        # Se tem placeholder [xxx], pedir para preencher
        import re
        placeholders = re.findall(r'\[(.+?)\]', topic)
        for ph in placeholders:
            value = input(f"  Preencha [{ph}]: ").strip()
            topic = topic.replace(f"[{ph}]", value)
        return topic

    return input("  Digite o tema: ").strip()


def suggest_by_calendar() -> tuple[str, str]:
    """Sugere tipo de carrossel baseado no dia da semana."""
    weekday = datetime.now().weekday()
    if weekday in EDITORIAL_CALENDAR:
        name, ctype, reason = EDITORIAL_CALENDAR[weekday]
        return name, ctype
    return "Tendência Interpretada", "tendencia"


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Designer AI — Gerador de Carrosséis v5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python generate_carousel.py --brand force-protocol --topic "creatina e hipertrofia"
  python generate_carousel.py --brand force-protocol --topic "creatina" --slides 9 --type tendencia
  python generate_carousel.py --brand force-protocol --topic "creatina" --auto
  python generate_carousel.py --list-brands
        """,
    )
    parser.add_argument("--brand",  metavar="SLUG",  help="Slug do perfil de marca")
    parser.add_argument("--topic",  metavar="TEMA",  help="Tema do carrossel")
    parser.add_argument("--slides", type=int, default=9, choices=[5, 7, 9, 12], help="Número de slides (default: 9)")
    parser.add_argument("--type",   default="tendencia", choices=["tendencia", "tese", "case", "previsao"], help="Tipo de carrossel")
    parser.add_argument("--cta",    default="", help="Texto do CTA (ex: 'Comenta GUIA')")
    parser.add_argument("--cover",  default="", help="Caminho para imagem de capa")
    parser.add_argument("--auto",   action="store_true", help="Modo automático (sem interação)")
    parser.add_argument("--open",   action="store_true", help="Abre a pasta após gerar")
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

    # Interativo: escolhe marca
    if not args.brand:
        slugs = BrandProfile.list_saved()
        if not slugs:
            _err("Nenhum perfil encontrado. Rode: python onboard.py")
            sys.exit(1)
        _h("DESIGNER AI — CARROSSEL v5")
        print("\n  Marcas disponíveis:")
        for i, s in enumerate(slugs, 1):
            print(f"    {i}. {s}")
        choice = input("\n  Escolha (número ou slug): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(slugs):
            args.brand = slugs[int(choice) - 1]
        else:
            args.brand = choice

    # Sugestão por calendário editorial
    auto_implied = args.auto
    if not args.type or args.type == "tendencia":
        cal_name, cal_type = suggest_by_calendar()
        print(f"\n  {DIM}Calendário editorial sugere:{RST} {BOLD}{cal_name}{RST} (hoje é {datetime.now().strftime('%A')})")
        if not auto_implied:
            print(f"  Usar sugestão? (Enter = sim, ou digite outro tipo): ", end="")
            type_input = input().strip()
            if not type_input:
                args.type = cal_type
            elif type_input in ("tendencia", "tese", "case", "previsao"):
                args.type = type_input

    # Interativo: escolhe tema
    if not args.topic:
        # Carrega marca pra pegar o nicho
        try:
            _brand = BrandProfile.load(args.brand)
            nicho = _brand.subniche or _brand.niche
        except Exception:
            nicho = "seu nicho"

        print(f"\n  Como quer definir o tema?")
        print(f"    1. Digitar meu tema")
        print(f"    2. Escolher dos prompts prontos")
        choice = input(f"\n  → ").strip()

        if choice == "2":
            args.topic = show_prompt_templates(nicho)
        else:
            print(f"  Qual o tema do carrossel?")
            args.topic = input("  → ").strip()

        if not args.topic:
            _err("Tema não pode ser vazio.")
            sys.exit(1)

    run(
        brand_slug=args.brand,
        topic=args.topic,
        n_slides=args.slides,
        carousel_type=args.type,
        cta_text=args.cta,
        auto_mode=args.auto,
        cover_image=args.cover,
        open_after=args.open,
    )


if __name__ == "__main__":
    main()
