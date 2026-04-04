"""
Suggester — chama Claude para gerar um BrandProfile completo
a partir de 3 inputs mínimos do cliente.
"""
from __future__ import annotations

import json
import os
import re

from anthropic import Anthropic

from designer.brand.profile import (
    AudienceProfile,
    BrandProfile,
    ColorPalette,
    Typography,
)

_SYSTEM = """\
Você é um estrategista de marca sênior e especialista em marketing digital brasileiro.
Sua função é, dado um produto/nicho mínimo, gerar um perfil de marca completo e estratégico.

REGRAS:
- SEMPRE retorne JSON válido seguindo exatamente o schema solicitado
- Baseie-se em dados reais do mercado brasileiro e comportamento digital
- Seja específico — nada genérico
- Cores devem refletir o posicionamento e a emoção da marca
- Tom de voz deve ser autêntico para o nicho
- Dores e desejos do público devem ser reais e específicos, não óbvios
"""

_SCHEMA = """\
{
  "slug": "nome-sem-espacos-lowercase",
  "client_name": "Nome Comercial Sugerido",
  "niche": "nicho principal",
  "subniche": "subnicho específico e lucrativo",
  "product": "{{PRODUCT}}",
  "goal": "{{GOAL}}",
  "tone": "descrição do tom de voz (ex: direto, técnico, motivacional)",
  "content_pillars": ["pilar 1", "pilar 2", "pilar 3"],
  "content_angles": [
    "Erro comum: ...",
    "Comparação: ...",
    "Urgência: ...",
    "Prova: ...",
    "Educação: ..."
  ],
  "suggested_formats": ["carrossel", "reels"],
  "audience": {
    "description": "descrição clara do público-alvo",
    "age_range": "ex: 25-40 anos",
    "pains": ["dor específica 1", "dor específica 2", "dor específica 3"],
    "desires": ["desejo 1", "desejo 2", "desejo 3"],
    "language": ["expressão que usam 1", "expressão 2", "expressão 3"]
  },
  "color_palette": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "text": "#FFFFFF"
  },
  "typography": {
    "headline": "Anton",
    "body": "Inter"
  },
  "market_gaps": ["lacuna de mercado 1", "lacuna 2"],
  "competitor_patterns": ["o que concorrentes fazem 1", "padrão 2"],
  "handle": ""
}"""


def suggest(
    product: str,
    audience_hint: str = "",
    goal: str = "vender mais",
) -> BrandProfile:
    """
    Chama Claude com o mínimo de informação e retorna um BrandProfile completo.

    Parameters
    ----------
    product       : O que o cliente vende (ex: "suplementos")
    audience_hint : Dica opcional sobre o público (ex: "homens que treinam")
    goal          : Objetivo principal ("vender mais" / "crescer o perfil" / etc.)
    """
    client = Anthropic()

    schema = (
        _SCHEMA
        .replace("{{PRODUCT}}", product)
        .replace("{{GOAL}}", goal)
    )

    audience_line = (
        f"PÚBLICO (hint do cliente): {audience_hint}"
        if audience_hint
        else "PÚBLICO: não informado — infira pelo produto e mercado"
    )

    prompt = f"""\
Com base nestas informações mínimas:

PRODUTO/NICHO: {product}
{audience_line}
OBJETIVO: {goal}

Gere um perfil de marca completo, estratégico e específico para o mercado brasileiro.

Retorne SOMENTE o JSON abaixo preenchido, sem texto extra:

{schema}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Remove blocos markdown se o modelo os incluir
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw.strip())

    # Garante campos opcionais
    data.setdefault("handle", "")
    data.setdefault("created_at", "")

    return BrandProfile._from_dict(data)
