"""
Slide Content Generator — gera conteúdo para slides internos do carrossel.

Estrutura padrão de 7 slides:
  Slide 1 — Capa         (gerado pelo carousel.py)
  Slide 2 — Problema     (o que está errado / por que isso importa)
  Slides 3-5 — Conteúdo  (3 pontos/dicas/insights numerados)
  Slide 6 — Prova/Dado   (stat, resultado, evidência)
  Slide 7 — CTA          (chamada para ação + handle)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

from designer.brand.profile import BrandProfile
from designer.copy.headlines import CopyResult


@dataclass
class SlideContent:
    number: int          # posição no carrossel (2–7)
    type: str            # "problem" | "content" | "proof" | "cta"
    headline: str        # título curto do slide (CAIXA ALTA)
    body: str            # texto do corpo (2–3 linhas)
    label: str = ""      # rótulo pequeno acima do headline (ex: "PONTO 1", "DADO")


def generate_slides(
    topic: str,
    brand: BrandProfile,
    copy: CopyResult,
    n_content: int = 3,
) -> list[SlideContent]:
    """
    Gera conteúdo para os slides internos (2–7) do carrossel.

    Parameters
    ----------
    topic      : tema do post
    brand      : perfil da marca
    copy       : CopyResult da capa (para manter coerência narrativa)
    n_content  : número de slides de conteúdo (padrão 3)
    """
    client = Anthropic()

    prompt = f"""
TEMA DO CARROSSEL: {topic}
MARCA: {brand.client_name} | NICHO: {brand.subniche}
TOM DE VOZ: {brand.tone}
PÚBLICO: {brand.audience.description}

CAPA JÁ CRIADA:
  Headline pt1: {copy.headline_part1}
  Headline pt2: {copy.headline_part2}

Gere o conteúdo para os slides INTERNOS do carrossel de Instagram (slides 2 a 7).
O carrossel deve ser uma sequência lógica que aprofunda o tema da capa.

Estrutura obrigatória:
- Slide 2 (problem): expande o problema/dor mencionado na capa
- Slides 3, 4, 5 (content): 3 insights/dicas numeradas, diretas e específicas
- Slide 6 (proof): dado, estatística ou resultado que valida o argumento
- Slide 7 (cta): chamada para ação clara + menção ao handle {brand.handle or "@" + brand.slug}

Regras:
- headline: máximo 6 palavras, CAIXA ALTA, impactante
- body: 2–3 frases curtas, tom direto, sem enrolação
- label: rótulo contextual curto (ex: "O PROBLEMA", "DICA 1", "DADO REAL", "PRÓXIMO PASSO")

Retorne SOMENTE este JSON (array de 6 objetos):
[
  {{
    "number": 2,
    "type": "problem",
    "label": "O PROBLEMA",
    "headline": "HEADLINE CURTA",
    "body": "Texto do corpo aqui. 2-3 frases diretas."
  }},
  {{
    "number": 3,
    "type": "content",
    "label": "DICA 1",
    "headline": "HEADLINE DA DICA",
    "body": "Explicação da dica. Prática e específica."
  }},
  {{
    "number": 4,
    "type": "content",
    "label": "DICA 2",
    "headline": "HEADLINE DA DICA",
    "body": "Explicação da dica. Prática e específica."
  }},
  {{
    "number": 5,
    "type": "content",
    "label": "DICA 3",
    "headline": "HEADLINE DA DICA",
    "body": "Explicação da dica. Prática e específica."
  }},
  {{
    "number": 6,
    "type": "proof",
    "label": "DADO REAL",
    "headline": "HEADLINE DO DADO",
    "body": "Estatística ou resultado concreto que valida o argumento."
  }},
  {{
    "number": 7,
    "type": "cta",
    "label": "PRÓXIMO PASSO",
    "headline": "CHAMADA PARA AÇÃO",
    "body": "CTA claro e natural. Sem pressão. Inclui {brand.handle or '@' + brand.slug}."
  }}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw.strip())

    return [
        SlideContent(
            number=d["number"],
            type=d["type"],
            headline=d["headline"].upper(),
            body=d["body"],
            label=d.get("label", "").upper(),
        )
        for d in data
    ]
