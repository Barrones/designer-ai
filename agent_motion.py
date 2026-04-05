#!/usr/bin/env python3
"""
Designer AI — Agente de Motion Ads (Remotion)
Para peças de propaganda animada quando não há footage disponível.

Pipeline:
  Claude gera copy + estrutura visual
  → Gera componente React (template Remotion)
  → npx remotion render → MP4
  → Google Drive

Quando usar:
  - Lançamento de produto
  - Promoção relâmpago / urgência
  - Anúncio sem footage real disponível
  - Propaganda com animação controlada

Uso:
    python agent_motion.py --brand force-protocol
    python agent_motion.py --brand force-protocol --topic "lançamento whey"
    python agent_motion.py --brand force-protocol --template dark_impact
    python agent_motion.py --brand force-protocol --dry-run
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


def run(brand_slug: str, topic: str = "", template: str = "", dry_run: bool = False) -> None:
    from anthropic import Anthropic
    from designer.brand.profile import BrandProfile
    from designer.research.topic_research import research_topic

    _h("DESIGNER AI — MOTION AD (REMOTION)")
    print(f"  Marca:    {brand_slug}")
    print(f"  Template: {template or 'auto'}")
    if dry_run:
        print(f"  {YELLOW}DRY-RUN — gera componente mas não renderiza{RST}")
    print()

    brand = BrandProfile.load(brand_slug)
    _ok(f"Marca: {brand.client_name}")

    # Direção criativa motion
    cd      = brand.creative_direction if hasattr(brand, "creative_direction") else {}
    motion  = cd.get("motion_ad", {})
    tmpl    = template or motion.get("remotion_template", "dark_impact")
    style   = motion.get("style", "dark minimalista")
    anim    = motion.get("animation", "texto com impacto")
    use_when= motion.get("use_when", "propaganda, urgência")
    duration= motion.get("duration_seconds", 15)

    print(f"  {DIM}Direção: {style}{RST}\n")

    # Tema
    if not topic:
        _step("Pesquisando tema ideal...")
        try:
            research = research_topic(brand.subniche or brand.niche)
            topic = research.tensao_central or research.resumo[:80]
        except Exception:
            topic = f"Lançamento — {brand.product}"
    _ok(f"Tema: {topic}")

    # Gera copy + estrutura do motion
    _h("ETAPA 1 — COPY E ESTRUTURA VISUAL")
    _step("Gerando com Claude...")

    client = Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""Crie o copy e estrutura visual de um Motion Ad de {duration}s para anúncio pago.

Marca: {brand.client_name}
Nicho: {brand.subniche or brand.niche}
Produto: {brand.product}
Tom: {brand.tone}
Tema/campanha: {topic}
Estilo visual: {style}
Animação: {anim}
Cor primária: {brand.color_palette.primary}
Cor accent: {brand.color_palette.secondary}

Estrutura (JSON puro):
{{
  "headline_1": "frase de impacto (3-5 palavras, UPPERCASE)",
  "headline_2": "complemento (max 8 palavras, UPPERCASE)",
  "subtext": "texto de apoio opcional (max 15 palavras)",
  "cta": "chamada para ação (max 5 palavras)",
  "animation_sequence": [
    {{"time": "0-3s", "element": "headline_1", "animation": "descrição da animação"}},
    {{"time": "3-8s", "element": "headline_2", "animation": "..."}},
    {{"time": "8-13s", "element": "subtext", "animation": "..."}},
    {{"time": "13-{duration}s", "element": "cta", "animation": "..."}}
  ],
  "background": "descrição do fundo (cor, textura, gradiente)",
  "mood": "descrição do mood visual geral"
}}"""}]
    )

    try:
        copy = json.loads(resp.content[0].text.strip())
    except Exception:
        import re
        m = re.search(r'\{.*\}', resp.content[0].text, re.DOTALL)
        copy = json.loads(m.group()) if m else {}

    _ok(f"Headline: {copy.get('headline_1')} / {copy.get('headline_2')}")
    _ok(f"CTA: {copy.get('cta')}")

    # Gera componente React Remotion
    _h("ETAPA 2 — COMPONENTE REACT (REMOTION)")
    _step("Gerando componente...")

    react_resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": f"""Gere um componente React completo para Remotion.

Copy:
{json.dumps(copy, ensure_ascii=False, indent=2)}

Paleta:
- Fundo: {brand.color_palette.primary}
- Texto: {brand.color_palette.text if hasattr(brand.color_palette, 'text') else '#FFFFFF'}
- Accent: {brand.color_palette.secondary}
- Destaque: {brand.color_palette.accent}

Duração: {duration} segundos (fps: 30, total frames: {duration * 30})
Tamanho: 1080x1920 (9:16 — Stories/Reels)

Regras:
- Use useCurrentFrame() e interpolate() do Remotion para animações
- Estilo: {style}
- Animação: {anim}
- Sem dependências externas além do remotion e react
- Fontes: use fonte do sistema ou Google Fonts via @import no style
- Exporte como default o componente principal

Gere APENAS o código TypeScript/TSX do componente, sem explicações."""}]
    )

    react_code = react_resp.content[0].text.strip()
    if react_code.startswith("```"):
        react_code = "\n".join(react_code.split("\n")[1:-1])

    # Salva output
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / "motion" / f"{brand_slug}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    component_path = output_dir / "MotionAd.tsx"
    component_path.write_text(react_code, encoding="utf-8")
    _ok(f"Componente salvo: {component_path}")

    meta = {
        "brand": brand_slug, "topic": topic, "template": tmpl,
        "copy": copy, "duration": duration, "generated_at": timestamp,
        "component": str(component_path),
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if dry_run:
        _h("CONCLUÍDO (DRY-RUN)")
        print(f"  Componente: {component_path}")
        _warn("Render Remotion ignorado (--dry-run)")
        print(f"\n  Para renderizar:")
        print(f"  cd remotion-project && npx remotion render MotionAd --output ../{output_dir}/motion_ad.mp4")
        return

    # Render com Remotion (se projeto existir)
    remotion_dir = Path("remotion-project")
    if remotion_dir.exists():
        _h("ETAPA 3 — RENDER REMOTION")
        _step("Renderizando MP4...")
        import shutil
        shutil.copy(component_path, remotion_dir / "src" / "MotionAd.tsx")
        result = os.system(
            f'cd "{remotion_dir}" && npx remotion render MotionAd '
            f'--output "../{output_dir}/motion_ad.mp4" --frames=0-{duration * 30}'
        )
        if result == 0:
            _ok(f"MP4 gerado: {output_dir}/motion_ad.mp4")
        else:
            _err("Render falhou. Verifique o projeto Remotion.")
    else:
        _warn("Projeto Remotion não encontrado. Componente gerado mas não renderizado.")
        print(f"  Para configurar Remotion:")
        print(f"  npx create-video@latest remotion-project")

    _h("CONCLUÍDO")
    print(f"  Pasta:     {output_dir}/")
    print(f"  Componente: MotionAd.tsx")
    print()


def main():
    parser = argparse.ArgumentParser(description="Designer AI — Motion Ads (Remotion)")
    parser.add_argument("--brand",    metavar="SLUG", help="Slug do perfil de marca")
    parser.add_argument("--topic",    metavar="TEMA", default="", help="Tema da peça (opcional)")
    parser.add_argument("--template", default="", help="Template Remotion (ex: dark_impact, epic_reveal)")
    parser.add_argument("--dry-run",  action="store_true", help="Gera componente mas não renderiza")
    args = parser.parse_args()

    if not args.brand:
        from designer.brand.profile import BrandProfile
        slugs = BrandProfile.list_saved()
        for i, s in enumerate(slugs, 1):
            print(f"  {i}. {s}")
        choice = input("\nEscolha a marca: ").strip()
        args.brand = slugs[int(choice)-1] if choice.isdigit() else choice

    run(brand_slug=args.brand, topic=args.topic, template=args.template, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
