"""
Brand Intelligence — pesquisa automática de tendências e dores do nicho.

Com nome + nicho + país, retorna:
  - Tendências atuais do nicho no país
  - Dores e objeções do público
  - Tom de voz recomendado
  - Pilares de conteúdo
  - Ângulos de alta conversão
  - Sugestões de temas para posts
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

COUNTRY_NAMES = {
    "BR": "Brasil", "IT": "Itália", "US": "Estados Unidos",
    "ES": "Espanha", "DE": "Alemanha", "FR": "França",
    "MX": "México", "PT": "Portugal", "UK": "Reino Unido",
}


@dataclass
class BrandIntel:
    trends: list[str]           # tendências do nicho
    pains: list[str]            # dores reais do público
    desires: list[str]          # desejos do público
    tone: str                   # tom de voz recomendado
    pillars: list[str]          # pilares de conteúdo
    angles: list[str]           # ângulos de alta conversão
    topic_suggestions: list[str] # sugestões de temas para posts
    audience_language: list[str] # vocabulário do público
    audience_description: str   # descrição do público
    accent_color: str = "#00D4FF"


def research_brand(
    brand_name: str,
    niche: str,
    country: str = "BR",
) -> BrandIntel:
    """
    Pesquisa automática: tendências + dores + ângulos para o nicho.

    Parameters
    ----------
    brand_name : nome da marca
    niche      : nicho/produto (ex: "cartão de crédito para negativados")
    country    : código do país (BR, IT, US...)

    Returns
    -------
    BrandIntel com tudo preenchido automaticamente
    """
    country_name = COUNTRY_NAMES.get(country.upper(), country)
    tavily_data  = _search_tavily(niche, country_name)
    intel        = _analyze_with_claude(brand_name, niche, country_name, tavily_data)
    return intel


def _search_tavily(niche: str, country_name: str) -> str:
    """Busca tendências e conteúdo do nicho via Tavily."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))

        queries = [
            f"tendências {niche} {country_name} 2025 2026",
            f"dores problemas público {niche} {country_name}",
            f"conteúdo viral {niche} Instagram TikTok {country_name}",
        ]

        results = []
        for q in queries:
            try:
                r = client.search(q, max_results=3, search_depth="basic")
                for item in r.get("results", []):
                    results.append(f"- {item.get('title', '')}: {item.get('content', '')[:300]}")
            except Exception:
                continue

        return "\n".join(results[:15]) if results else ""
    except Exception:
        return ""


def _analyze_with_claude(
    brand_name: str,
    niche: str,
    country_name: str,
    tavily_data: str,
) -> BrandIntel:
    """Claude analisa os dados e gera o perfil completo da marca."""
    client = Anthropic()

    research_section = f"\nDADOS DE PESQUISA WEB:\n{tavily_data}" if tavily_data else ""

    prompt = f"""Você é um estrategista de conteúdo digital especializado em Instagram e TikTok.

MARCA: {brand_name}
NICHO: {niche}
PAÍS: {country_name}
{research_section}

Com base no nicho e no país, gere um perfil completo de inteligência de mercado.

Pense como um especialista que conhece profundamente:
- O que mantém esse público acordado à noite (dores reais, não genéricas)
- O que eles mais desejam mas têm vergonha de admitir
- Quais tendências estão dominando esse nicho agora
- Que tipo de linguagem esse público usa no dia a dia
- Quais ângulos de conteúdo geram mais engajamento nesse nicho

Retorne SOMENTE este JSON:
{{
  "trends": ["tendência 1 específica e atual", "tendência 2", "tendência 3", "tendência 4", "tendência 5"],
  "pains": ["dor real e específica 1", "dor 2", "dor 3", "dor 4", "dor 5", "dor 6"],
  "desires": ["desejo 1", "desejo 2", "desejo 3", "desejo 4"],
  "tone": "descrição do tom de voz ideal para este nicho e público (2-3 adjetivos + explicação curta)",
  "pillars": ["pilar 1", "pilar 2", "pilar 3", "pilar 4"],
  "angles": ["ângulo de conteúdo 1 (ex: mito vs verdade)", "ângulo 2", "ângulo 3", "ângulo 4", "ângulo 5"],
  "topic_suggestions": [
    "tema específico para post 1",
    "tema específico para post 2",
    "tema específico para post 3",
    "tema específico para post 4",
    "tema específico para post 5"
  ],
  "audience_language": ["expressão que o público usa 1", "expressão 2", "expressão 3", "expressão 4"],
  "audience_description": "descrição em 1-2 frases de quem é esse público específico",
  "accent_color": "#hexcode que representa visualmente este nicho (ex: #00D4FF para tech, #FF6B35 para fitness)"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw.strip())

    return BrandIntel(
        trends=data.get("trends", []),
        pains=data.get("pains", []),
        desires=data.get("desires", []),
        tone=data.get("tone", ""),
        pillars=data.get("pillars", []),
        angles=data.get("angles", []),
        topic_suggestions=data.get("topic_suggestions", []),
        audience_language=data.get("audience_language", []),
        audience_description=data.get("audience_description", ""),
        accent_color=data.get("accent_color", "#00D4FF"),
    )
