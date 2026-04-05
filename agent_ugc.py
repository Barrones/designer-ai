#!/usr/bin/env python3
"""
Designer AI — Agente UGC
Lê vídeos de criadores → transcreve → gera roteiro no estilo deles → Topview → Drive

Pipeline:
  Vídeos de referência (creator_profiles/<creator>/videos/)
  → Transcrição (Whisper/Groq)
  → Análise de estilo (Claude)
  → Roteiro UGC calibrado por nicho e marca
  → Topview (text2video ou avatar)
  → Google Drive

Uso:
    python agent_ugc.py --brand force-protocol --creator jeffnippard
    python agent_ugc.py --brand force-protocol --creator kallaway --format discovery
    python agent_ugc.py --brand force-protocol --creator jeffnippard --variations 3
    python agent_ugc.py --list-creators
    python agent_ugc.py --transcribe jeffnippard
    python agent_ugc.py --brand force-protocol --creator jeffnippard --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

BOLD  = "\033[1m"; RST = "\033[0m"; GREEN = "\033[92m"
YELLOW= "\033[93m"; RED = "\033[91m"; CYAN = "\033[96m"; DIM = "\033[2m"
SEP2  = "═" * 60

def _h(t): print(f"\n{SEP2}\n  {BOLD}{t}{RST}\n{SEP2}")
def _ok(t): print(f"  {GREEN}✓{RST}  {t}")
def _warn(t): print(f"  {YELLOW}⚠{RST}  {t}")
def _err(t): print(f"  {RED}✗{RST}  {t}")
def _step(t): print(f"  {CYAN}→{RST}  {t}")


def run(
    brand_slug: str,
    creator: str,
    topic: str = "",
    fmt: str = "review",
    duration: int = 30,
    variations: int = 1,
    dry_run: bool = False,
) -> None:
    from designer.ugc.script_writer import generate_script
    from designer.ugc.transcriber import get_all_creators_summary
    from designer.brand.profile import BrandProfile
    from designer.research.topic_research import research_topic

    _h("DESIGNER AI — AGENTE UGC")
    print(f"  Marca:    {brand_slug}")
    print(f"  Criador:  @{creator}")
    print(f"  Formato:  {fmt} | {duration}s | {variations} variação(ões)")
    if dry_run:
        print(f"  {YELLOW}DRY-RUN — gera roteiro mas não renderiza vídeo{RST}")
    print()

    brand = BrandProfile.load(brand_slug)
    _ok(f"Marca: {brand.client_name} ({brand.subniche or brand.niche})")

    # Tema
    if not topic:
        _step("Pesquisando tema ideal para o nicho...")
        try:
            research = research_topic(brand.subniche or brand.niche)
            topic = research.tensao_central or research.resumo[:100]
        except Exception:
            topic = f"{brand.product} — como usar corretamente"
    _ok(f"Tema: {topic}")

    # Gera roteiro(s)
    _h("ETAPA 1 — ROTEIRO UGC")
    _step(f"Modelando estilo de @{creator}...")

    try:
        scripts = generate_script(
            brand_slug=brand_slug,
            topic=topic,
            creator=creator,
            format=fmt,
            duration=duration,
            variations=variations,
        )
    except ValueError as e:
        _err(str(e))
        sys.exit(1)

    for script in scripts:
        var = script.get("variation", 1)
        _ok(f"Variação {var} gerada ({script.get('word_count', 0)} palavras)")
        print(f"\n  {DIM}Gancho:{RST}")
        for block in script.get("script", []):
            if block.get("block") == "gancho":
                print(f"    \"{block.get('fala', '')}\"")
        print(f"  {DIM}Estilo aplicado:{RST} {script.get('creator_match', '')[:80]}")

    # Salva roteiros
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / "ugc" / f"{brand_slug}_{creator}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, script in enumerate(scripts, 1):
        script_path = output_dir / f"script_v{i}.json"
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

        # Salva também o texto corrido para TTS
        full_text = script.get("full_text", "")
        if full_text:
            (output_dir / f"script_v{i}.txt").write_text(full_text, encoding="utf-8")

    _ok(f"Roteiros salvos em {output_dir}/")

    if dry_run:
        _h("CONCLUÍDO (DRY-RUN)")
        print(f"  Pasta:    {output_dir}/")
        print(f"  Roteiros: {len(scripts)} variação(ões)")
        _warn("Geração de vídeo ignorada (--dry-run)")
        print(f"\n  Próximo passo:")
        print(f"  python agent_ugc.py --brand {brand_slug} --creator {creator} [sem --dry-run]")
        return

    # Gera vídeo com Topview
    _h("ETAPA 2 — VÍDEO (TOPVIEW)")

    topview_scripts = Path(__file__).parent / "topview" / "scripts"
    if not topview_scripts.exists():
        _warn("Scripts Topview não encontrados. Pulando geração de vídeo.")
        _h("CONCLUÍDO")
        print(f"  Roteiros prontos em: {output_dir}/")
        return

    for i, script in enumerate(scripts, 1):
        full_text = script.get("full_text", "")
        if not full_text:
            continue

        _step(f"Gerando vídeo variação {i}...")

        # Usa text2video do Topview
        video_output = output_dir / f"ugc_v{i}.mp4"
        cmd = (
            f'cd "{topview_scripts}" && '
            f'python video_gen.py run --type t2v '
            f'--model "Seedance 1.5 Pro" '
            f'--prompt "{full_text[:200]}" '
            f'--output "{video_output}" 2>&1'
        )
        result = os.system(cmd)

        if result == 0 and video_output.exists():
            _ok(f"Vídeo {i}: {video_output}")
        else:
            _warn(f"Vídeo {i} falhou. Roteiro disponível em script_v{i}.txt")

    # Upload para Drive
    _h("ETAPA 3 — GOOGLE DRIVE")
    try:
        from designer.delivery.drive import upload_carousel
        mp4s = list(output_dir.glob("*.mp4"))
        if mp4s:
            _step(f"Enviando {len(mp4s)} vídeo(s) para o Drive...")
            urls = upload_carousel(
                files=[str(p) for p in mp4s],
                brand_slug=brand_slug,
                topic=topic,
                content_type="ugc",
            )
            for url in urls:
                _ok(f"Drive: {url}")
        else:
            _warn("Nenhum MP4 para enviar ao Drive")
    except Exception as e:
        _warn(f"Drive indisponível: {e}")

    _h("CONCLUÍDO")
    print(f"  Pasta:     {output_dir}/")
    print(f"  Criador:   @{creator}")
    print(f"  Roteiros:  {len(scripts)} variação(ões)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Designer AI — Agente UGC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # UGC review no estilo jeffnippard
  python agent_ugc.py --brand force-protocol --creator jeffnippard

  # 3 variações formato descoberta
  python agent_ugc.py --brand force-protocol --creator kallaway --format discovery --variations 3

  # Só gera roteiro (sem vídeo)
  python agent_ugc.py --brand force-protocol --creator jeffnippard --dry-run

  # Transcreve vídeos de um criador novo
  python agent_ugc.py --transcribe nome-do-criador

  # Lista criadores disponíveis
  python agent_ugc.py --list-creators
        """,
    )
    parser.add_argument("--brand",       metavar="SLUG",   help="Slug do perfil de marca")
    parser.add_argument("--creator",     metavar="NOME",   help="Criador de referência (pasta em creator_profiles/)")
    parser.add_argument("--topic",       metavar="TEMA",   default="", help="Tema do vídeo (opcional)")
    parser.add_argument("--format",      default="review",
                        choices=["review", "problem", "discovery", "comparison"],
                        help="Formato do roteiro UGC (default: review)")
    parser.add_argument("--duration",    type=int, default=30, help="Duração em segundos (default: 30)")
    parser.add_argument("--variations",  type=int, default=1, help="Número de variações do roteiro (default: 1)")
    parser.add_argument("--dry-run",     action="store_true", help="Só gera roteiro, não renderiza vídeo")
    parser.add_argument("--list-creators", action="store_true", help="Lista criadores disponíveis")
    parser.add_argument("--transcribe",  metavar="CRIADOR", help="Transcreve vídeos de um criador")
    args = parser.parse_args()

    if args.list_creators:
        from designer.ugc.transcriber import get_all_creators_summary
        print(get_all_creators_summary())
        return

    if args.transcribe:
        from designer.ugc.transcriber import transcribe_creator
        _h(f"TRANSCREVENDO @{args.transcribe}")
        transcribe_creator(args.transcribe)
        return

    if not args.brand:
        from designer.brand.profile import BrandProfile
        slugs = BrandProfile.list_saved()
        print("\nMarcas disponíveis:")
        for i, s in enumerate(slugs, 1):
            print(f"  {i}. {s}")
        choice = input("\nEscolha: ").strip()
        args.brand = slugs[int(choice)-1] if choice.isdigit() else choice

    if not args.creator:
        from designer.ugc.transcriber import list_creators
        creators = list_creators()
        if not creators:
            print("Nenhum criador encontrado. Adicione vídeos em creator_profiles/<nome>/videos/")
            sys.exit(1)
        print("\nCriadores disponíveis:")
        for i, c in enumerate(creators, 1):
            print(f"  {i}. {c}")
        choice = input("\nEscolha: ").strip()
        args.creator = creators[int(choice)-1] if choice.isdigit() else choice

    run(
        brand_slug=args.brand,
        creator=args.creator,
        topic=args.topic,
        fmt=args.format,
        duration=args.duration,
        variations=args.variations,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
