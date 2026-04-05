"""
Topic Research — pesquisa dados reais sobre um tema específico.

Usado quando o usuário escolhe o modo 2 (criar narrativa a partir de insight).
Busca dados, estatísticas, fontes e fatos verificáveis sobre o tema
antes de gerar qualquer conteúdo.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TopicResearch:
    tema: str
    resumo: str                    # 1 parágrafo resumindo o fenômeno
    dados: list[str]               # fatos com número + fonte + ano
    tendencias: list[str]          # tendências relacionadas
    angulos: list[str]             # ângulos narrativos possíveis
    fontes: list[str]              # URLs/nomes das fontes consultadas
    tensao_central: str            # a fricção/tensão principal do tema
    publico_afetado: str           # quem é impactado por esse tema


def research_topic(
    topic: str,
    niche: str = "",
    country: str = "BR",
) -> TopicResearch:
    """
    Pesquisa um tema específico usando Tavily + Claude.

    Parameters
    ----------
    topic   : o insight ou tema do usuário
    niche   : nicho da marca (para contextualizar a busca)
    country : país de referência
    """
    # 1. Busca web com Tavily
    tavily_data = _search_tavily(topic, niche, country)

    # 2. Claude analisa e estrutura os dados
    research = _analyze_with_claude(topic, niche, tavily_data)

    return research


def _search_tavily(topic: str, niche: str, country: str) -> str:
    """Busca dados reais sobre o tema via Tavily."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return "[Tavily não configurado — usando apenas conhecimento base]"

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)

        # Query principal
        query = f"{topic} dados estatísticas Brasil 2024 2025"
        if niche:
            query = f"{topic} {niche} dados estatísticas Brasil"

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True,
        )

        parts = []
        if results.get("answer"):
            parts.append(f"RESUMO DA PESQUISA:\n{results['answer']}")

        parts.append("\nFONTES ENCONTRADAS:")
        for r in results.get("results", [])[:8]:
            title = r.get("title", "")
            content = r.get("content", "")[:500]
            url = r.get("url", "")
            parts.append(f"\n[{title}]({url})\n{content}")

        # Segunda busca: tendências e comportamento
        query2 = f"{topic} tendência comportamento por que crescimento"
        results2 = client.search(
            query=query2,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )

        if results2.get("answer"):
            parts.append(f"\nTENDÊNCIAS:\n{results2['answer']}")

        for r in results2.get("results", [])[:4]:
            title = r.get("title", "")
            content = r.get("content", "")[:300]
            parts.append(f"\n- {title}: {content}")

        return "\n".join(parts)

    except Exception as e:
        return f"[Pesquisa Tavily falhou: {e}]"


def _analyze_with_claude(topic: str, niche: str, tavily_data: str) -> TopicResearch:
    """Claude analisa os dados e estrutura a pesquisa."""
    client = Anthropic()

    prompt = f"""
TEMA PARA PESQUISA: {topic}
NICHO (se houver): {niche or "geral"}

DADOS DA PESQUISA WEB:
{tavily_data}

---

Analise os dados acima e extraia informações estruturadas sobre o tema.
Seu objetivo é fornecer uma base sólida de dados reais para criar um carrossel de Instagram.

REGRAS:
- Só inclua dados que têm fonte verificável nos resultados acima
- Se não encontrou dado específico, diga "dado não encontrado" — NUNCA invente
- Prefira dados do Brasil quando disponíveis
- Cada dado deve ter: número + fonte + ano/período

Retorne SOMENTE este JSON:
{{
  "tema": "{topic}",
  "resumo": "1 parágrafo resumindo o fenômeno central — o que está acontecendo e por que importa",
  "dados": [
    "dado 1 com número + fonte + ano",
    "dado 2 com número + fonte + ano",
    "dado 3 com número + fonte + ano"
  ],
  "tendencias": [
    "tendência 1 relacionada ao tema",
    "tendência 2 relacionada"
  ],
  "angulos": [
    "ângulo narrativo 1 — ex: contraste geracional",
    "ângulo narrativo 2 — ex: fenômeno cultural",
    "ângulo narrativo 3 — ex: dado surpreendente"
  ],
  "fontes": [
    "Nome da fonte 1",
    "Nome da fonte 2"
  ],
  "tensao_central": "A principal fricção/tensão/contradição do tema — o que gera debate",
  "publico_afetado": "Quem é diretamente impactado por esse fenômeno"
}}
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

    return TopicResearch(
        tema=data.get("tema", topic),
        resumo=data.get("resumo", ""),
        dados=data.get("dados", []),
        tendencias=data.get("tendencias", []),
        angulos=data.get("angulos", []),
        fontes=data.get("fontes", []),
        tensao_central=data.get("tensao_central", ""),
        publico_afetado=data.get("publico_afetado", ""),
    )
