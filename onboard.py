#!/usr/bin/env python3
"""
Designer AI — Onboarding de marca

Uso:
    python onboard.py              → cria novo perfil
    python onboard.py --list       → lista perfis salvos
    python onboard.py --load slug  → mostra perfil existente
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Permite rodar da raiz do projeto sem instalar o pacote
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from designer.brand.profile import BrandProfile
from designer.brand.suggester import suggest

# ---------------------------------------------------------------------------
# Helpers de display
# ---------------------------------------------------------------------------

SEP  = "─" * 56
SEP2 = "═" * 56

def _h(title: str) -> None:
    print(f"\n{SEP2}")
    print(f"  {title}")
    print(SEP2)

def _section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title.upper()}")
    print(SEP)

def _bullets(items: list[str], indent: int = 4) -> None:
    for item in items:
        print(" " * indent + f"→  {item}")

def _field(label: str, value: str, width: int = 20) -> None:
    print(f"  {label:<{width}} {value}")

def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"\n  {prompt}{suffix}\n  > ").strip()
    return val or default

def _choose(prompt: str, options: list[str]) -> str:
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    [{i}] {opt}")
    while True:
        raw = input("  > ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        # Allow typing the value directly
        matches = [o for o in options if o.lower().startswith(raw.lower())]
        if len(matches) == 1:
            return matches[0]
        print("  Opção inválida. Tente novamente.")


# ---------------------------------------------------------------------------
# Display de um BrandProfile
# ---------------------------------------------------------------------------

def display_profile(p: BrandProfile) -> None:
    _h(f"PERFIL DE MARCA — {p.client_name.upper()}")

    _section("Identidade")
    _field("Nicho:",        p.niche)
    _field("Subnicho:",     p.subniche)
    _field("Produto:",      p.product)
    _field("Objetivo:",     p.goal)
    _field("Tom de voz:",   p.tone)
    _field("Handle:",       p.handle or "(não definido)")

    _section("Paleta de cores")
    _field("Principal:",   p.color_palette.primary)
    _field("Secundária:",  p.color_palette.secondary)
    _field("Destaque:",    p.color_palette.accent)
    _field("Texto:",       p.color_palette.text)

    _section("Pilares de conteúdo")
    _bullets(p.content_pillars)

    _section("Ângulos de conteúdo")
    _bullets(p.content_angles)

    _section("Público-alvo")
    _field("Descrição:",   p.audience.description)
    _field("Faixa etária:", p.audience.age_range)
    print()
    print("  Dores:")
    _bullets(p.audience.pains, 6)
    print("\n  Desejos:")
    _bullets(p.audience.desires, 6)
    print("\n  Linguagem que usam:")
    _bullets(p.audience.language, 6)

    _section("Inteligência de mercado")
    print("  Lacunas de oportunidade:")
    _bullets(p.market_gaps, 6)
    print("\n  O que concorrentes fazem:")
    _bullets(p.competitor_patterns, 6)

    _section("Formatos sugeridos")
    _bullets(p.suggested_formats)


# ---------------------------------------------------------------------------
# Fluxo principal de onboarding
# ---------------------------------------------------------------------------

def run_onboarding() -> None:
    _h("DESIGNER AI — ONBOARDING DE MARCA")
    print("\n  Vamos montar o perfil da sua marca em 3 perguntas.")
    print("  O sistema pesquisa o mercado e sugere tudo automaticamente.\n")

    # --- 3 perguntas mínimas ---
    product = _ask("1. O que você vende? (produto, serviço ou nicho)")
    while not product:
        print("  Campo obrigatório.")
        product = _ask("1. O que você vende?")

    audience_hint = _ask(
        "2. Para quem? (pode deixar em branco — o sistema infere)",
        default="",
    )

    goal = _choose(
        "3. Qual o principal objetivo?",
        [
            "Vender mais",
            "Crescer o perfil",
            "Educar o público",
            "Construir autoridade",
        ],
    )

    # --- Pesquisa e geração ---
    print(f"\n{SEP}")
    print("  Pesquisando o mercado e gerando perfil de marca...")
    print(f"{SEP}\n")

    try:
        profile = suggest(
            product=product,
            audience_hint=audience_hint,
            goal=goal,
        )
    except Exception as exc:
        print(f"\n  ERRO ao gerar perfil: {exc}")
        sys.exit(1)

    # --- Mostra a sugestão ---
    display_profile(profile)

    # --- Confirmação ---
    print(f"\n{SEP2}")
    print("  Esse perfil está correto?")
    print("  [s] Salvar e usar    [n] Cancelar    [h] Editar handle")
    print(SEP2)

    while True:
        choice = input("  > ").strip().lower()

        if choice == "n":
            print("\n  Cancelado. Rode novamente para gerar outro perfil.")
            sys.exit(0)

        if choice == "h":
            handle = _ask("Handle do Instagram (ex: @minhemarca)")
            profile.handle = handle if handle.startswith("@") else f"@{handle}"
            print(f"  Handle definido: {profile.handle}")
            continue

        if choice in ("s", ""):
            path = profile.save()
            print(f"\n  Perfil salvo em: {path}")
            print(f"\n  Próximo passo:")
            print(f"    python onboard.py --load {profile.slug}   (ver perfil)")
            print(f"    python generate.py --brand {profile.slug}  (gerar post)")
            break

        print("  Digite s, n ou h.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Designer AI — Onboarding de marca")
    parser.add_argument("--list",  action="store_true", help="Lista perfis salvos")
    parser.add_argument("--load",  metavar="SLUG",      help="Mostra um perfil salvo")
    args = parser.parse_args()

    if args.list:
        slugs = BrandProfile.list_saved()
        if not slugs:
            print("Nenhum perfil salvo ainda. Rode: python onboard.py")
        else:
            print("Perfis salvos:")
            for s in slugs:
                print(f"  → {s}")
        return

    if args.load:
        try:
            p = BrandProfile.load(args.load)
        except FileNotFoundError:
            print(f"Perfil '{args.load}' não encontrado. Rode: python onboard.py --list")
            sys.exit(1)
        display_profile(p)
        return

    run_onboarding()


if __name__ == "__main__":
    main()
