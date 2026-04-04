"""
Trend Research — sugere temas de post com base em tendências reais do nicho.

Fontes (em ordem de prioridade):
  1. Tavily   — busca web semântica (o que está sendo publicado/discutido agora)
  2. pytrends — Google Trends (interesse de busca real, validação)

Retorna lista de TopicSuggestion prontos para passar ao generate.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

from designer.brand.profile import BrandProfile


@dataclass
class TopicSuggestion:
    topic: str          # ex: "por que 90% das pessoas treinam errado"
    angle: str          # ex: "mito vs. realidade"
    formula: str        # ex: "F4 — Provocação Pura"
    trend_score: int    # 0–100 (estimado)
    source: str         # "tavily" | "pytrends" | "claude"


def suggest_topics(
    brand: BrandProfile,
    n: int = 5,
) -> list[TopicSuggestion]:
    """
    Retorna N sugestões de temas com base nas tendências do nicho da marca.

    Fluxo:
      1. Tavily busca o que está em alta no nicho agora
      2. pytrends valida interesse de busca (opcional, fallback gracioso)
      3. Claude analisa os dados e gera temas específicos para a marca
    """
    raw_trends = _fetch_tavily_trends(brand)
    google_data = _fetch_pytrends(brand)
    suggestions = _generate_topics_with_claude(brand, raw_trends, google_data, n)
    return suggestions


# ---------------------------------------------------------------------------
# Fonte 1 — Tavily
# ---------------------------------------------------------------------------

def _fetch_tavily_trends(brand: BrandProfile) -> str:
    """Busca o que está sendo publicado/discutido no nicho agora."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return ""

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)

        query = (
            f"tendências conteúdo Instagram {brand.subniche} {brand.niche} "
            f"2026 viral engajamento dicas estratégia"
        )

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_answer=True,
        )

        parts = []
        if results.get("answer"):
            parts.append(f"RESUMO: {results['answer']}")

        for r in results.get("results", [])[:6]:
            title   = r.get("title", "")
            content = r.get("content", "")[:400]
            parts.append(f"- {title}: {content}")

        return "\n".join(parts)

    except Exception as e:
        return f"[Tavily indisponível: {e}]"


# ---------------------------------------------------------------------------
# Fonte 2 — Google Trends (pytrends)
# ---------------------------------------------------------------------------

def _fetch_pytrends(brand: BrandProfile) -> str:
    """Valida interesse de busca real via Google Trends."""
    try:
        from pytrends.request import TrendReq

        keywords = [brand.subniche, brand.niche, brand.product]
        keywords = [k for k in keywords if k][:3]

        pytrends = TrendReq(hl="pt-BR", tz=-180, timeout=(10, 25))
        pytrends.build_payload(keywords, geo="BR", timeframe="today 1-m")

        interest_df = pytrends.interest_over_time()
        related     = pytrends.related_queries()

        lines = []

        if not interest_df.empty:
            for kw in keywords:
                if kw in interest_df.columns:
                    avg  = round(interest_df[kw].mean(), 1)
                    peak = round(interest_df[kw].max(), 1)
                    lines.append(f"- {kw}: interesse médio {avg}/100, pico {peak}/100")

        rising_queries = []
        for kw in keywords:
            if kw in related and related[kw].get("rising") is not None:
                df = related[kw]["rising"]
                if not df.empty:
                    for _, row in df.head(5).iterrows():
                        rising_queries.append(row["query"])

        if rising_queries:
            lines.append(f"Buscas em alta: {', '.join(rising_queries[:8])}")

        return "\n".join(lines) if lines else ""

    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Síntese — Claude analisa e gera temas específicos para a marca
# ---------------------------------------------------------------------------

def _generate_topics_with_claude(
    brand: BrandProfile,
    tavily_data: str,
    trends_data: str,
    n: int,
) -> list[TopicSuggestion]:
    """Claude analisa os dados de tendência e gera temas prontos para o copy."""
    client = Anthropic()

    context_parts = []
    if tavily_data:
        context_parts.append(f"=== O QUE ESTÁ EM ALTA AGORA (Tavily) ===\n{tavily_data}")
    if trends_data:
        context_parts.append(f"=== INTERESSE DE BUSCA (Google Trends BR) ===\n{trends_data}")

    trends_context = "\n\n".join(context_parts) or "Sem dados externos disponíveis."

    prompt = f"""
MARCA: {brand.client_name}
NICHO: {brand.niche} | SUBNICHO: {brand.subniche}
PRODUTO: {brand.product}
TOM DE VOZ: {brand.tone}
PILARES DE CONTEÚDO: {", ".join(brand.content_pillars)}
DORES DO PÚBLICO: {" | ".join(brand.audience.pains)}
PÚBLICO: {brand.audience.description} ({brand.audience.age_range})

DADOS DE TENDÊNCIA:
{trends_context}

---

Com base nos dados acima, gere {n} sugestões de tema para posts de carrossel no Instagram.
Cada tema deve:
- Ser específico para o nicho e ressoar com as dores do público
- Ter potencial de alto engajamento (curiosidade, polêmica, utilidade)
- Se encaixar naturalmente em uma das 4 fórmulas:
  F1=Contexto+Provocação, F2=Afirmação+Pergunta, F3=Notícia+Dado, F4=Provocação Pura

Retorne SOMENTE este JSON (array de {n} objetos):
[
  {{
    "topic": "tema específico e direto (como você digitaria no generate.py)",
    "angle": "ângulo criativo em 1 frase",
    "formula": "F1|F2|F3|F4",
    "trend_score": 0-100,
    "source": "tavily|pytrends|claude"
  }}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    import json, re
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw.strip())

    return [
        TopicSuggestion(
            topic=d["topic"],
            angle=d["angle"],
            formula=d["formula"],
            trend_score=int(d.get("trend_score", 70)),
            source=d.get("source", "claude"),
        )
        for d in data
    ]
