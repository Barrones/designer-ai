"""
UGC Script Writer — gera roteiros no estilo de criadores reais.

Usa transcrições de referência para calibrar:
- Tom de voz (técnico, casual, energético)
- Estrutura do vídeo (gancho, desenvolvimento, CTA)
- Vocabulário e expressões naturais
- Duração e ritmo de fala

Saída: roteiro com timecodes + sugestão de cena visual por bloco.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

from designer.ugc.transcriber import get_transcriptions, get_all_creators_summary, list_creators


def generate_script(
    brand_slug: str,
    topic: str,
    creator: str,
    format: str = "review",       # review | problem | discovery | comparison
    duration: int = 30,            # segundos
    variations: int = 1,
) -> list[dict]:
    """
    Gera roteiro(s) UGC no estilo do criador escolhido.

    Returns lista de dicts com:
        - script: roteiro completo com timecodes
        - style_notes: observações sobre o estilo usado
        - visual_cues: sugestões de cena por bloco
        - word_count: contagem de palavras (guia de duração)
    """
    from designer.brand.profile import BrandProfile

    client = Anthropic()
    brand  = BrandProfile.load(brand_slug)

    # Carrega transcrições do criador
    try:
        transcriptions = get_transcriptions(creator)
    except FileNotFoundError:
        raise ValueError(
            f"Criador '{creator}' não encontrado ou sem transcrições.\n"
            f"{get_all_creators_summary()}"
        )

    # Direção criativa da marca para UGC
    cd  = brand.creative_direction if hasattr(brand, "creative_direction") else {}
    ugc = cd.get("ugc", {})

    format_instructions = {
        "review":      "Estilo REVIEW: pessoa testou o produto, conta a experiência real. Tom pessoal, honesto, com dados concretos no meio.",
        "problem":     "Estilo PROBLEMA: começa com o problema que o avatar vivia antes de encontrar o produto. Identificação emocional primeiro.",
        "discovery":   "Estilo DESCOBERTA: 'não sabia que existia isso...'. Tom de surpresa genuína, curiosidade.",
        "comparison":  "Estilo COMPARAÇÃO: produto vs. alternativa anterior. Dados, diferenças concretas, por que mudou.",
    }

    system = f"""Você é um roteirista especializado em UGC (User Generated Content) para anúncios pagos no Instagram e TikTok.

Seu trabalho é criar roteiros que:
1. Parecem gravados por uma pessoa real, não por uma marca
2. Modelam o estilo de fala e estrutura do criador de referência
3. Convertem — são construídos para anúncio, não para conteúdo orgânico
4. Passam pelo algoritmo como conteúdo orgânico

REGRAS CRÍTICAS:
- NUNCA usar linguagem corporativa ou de marca
- NUNCA começar com o nome do produto
- SEMPRE começar com uma situação ou problema do avatar
- Tom de conversa real, como se estivesse falando com um amigo
- Dados e especificidades são bem-vindos (dão credibilidade)
- Sem transições artificiais ("além disso", "por outro lado")
- Falar na primeira pessoa sempre"""

    results = []

    for i in range(variations):
        variation_note = f"\n\nEsta é a variação {i+1} de {variations}. Use um ângulo diferente das anteriores." if variations > 1 else ""

        prompt = f"""## REFERÊNCIA DE ESTILO — @{creator}

{transcriptions}

---

## BRIEFING DO ROTEIRO

**Marca:** {brand.client_name}
**Nicho:** {brand.subniche or brand.niche}
**Tom da marca:** {brand.tone}
**Produto/serviço:** {brand.product}
**Tema do vídeo:** {topic}
**Duração alvo:** {duration} segundos (~{int(duration * 2.5)} palavras faladas)
**Formato:** {format_instructions.get(format, format_instructions['review'])}

**Público-alvo:** {brand.audience.description if hasattr(brand, 'audience') and brand.audience else ''}

**Dores do público:**
{chr(10).join(f'- {p}' for p in (brand.audience.pains if hasattr(brand, 'audience') and brand.audience else []))}

**Desejos do público:**
{chr(10).join(f'- {d}' for d in (brand.audience.desires if hasattr(brand, 'audience') and brand.audience else []))}

{f"**Direção criativa UGC:** {ugc}" if ugc else ""}
{variation_note}

---

## INSTRUÇÃO

Analise o estilo do criador @{creator} nas transcrições acima. Identifique:
- Como ele abre o vídeo (gancho)
- Como estrutura o desenvolvimento
- Vocabulário específico que usa
- Ritmo e cadência das frases
- Como faz o CTA

Agora crie um roteiro UGC de {duration} segundos para {brand.client_name} sobre "{topic}", modelando esse estilo mas adaptado para o produto e público da marca.

Responda em JSON puro:
{{
  "script": [
    {{
      "block": "gancho",
      "timecode": "0-5s",
      "fala": "texto exato que a pessoa fala",
      "visual": "descrição da cena/ação na câmera"
    }},
    {{
      "block": "desenvolvimento",
      "timecode": "5-20s",
      "fala": "...",
      "visual": "..."
    }},
    {{
      "block": "prova",
      "timecode": "20-25s",
      "fala": "...",
      "visual": "..."
    }},
    {{
      "block": "cta",
      "timecode": "25-{duration}s",
      "fala": "...",
      "visual": "..."
    }}
  ],
  "style_notes": "observações sobre o estilo do criador que você aplicou",
  "full_text": "roteiro completo corrido (sem timecodes) para leitura/TTS",
  "word_count": 0,
  "creator_match": "como o roteiro reflete o estilo de @{creator}"
}}"""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        text = resp.content[0].text.strip()
        try:
            data = json.loads(text)
        except Exception:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            data = json.loads(match.group()) if match else {"script": [], "full_text": text}

        # Conta palavras do texto completo
        full_text = data.get("full_text", "")
        data["word_count"] = len(full_text.split())
        data["variation"] = i + 1
        data["creator"] = creator
        data["brand"] = brand_slug
        data["topic"] = topic
        data["format"] = format
        data["duration_target"] = duration

        results.append(data)

    return results
