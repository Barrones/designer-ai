"""
Ferramentas de pesquisa de mercado para o agente copywriter.

Fontes:
- Google Trends (pytrends) — tendências por palavra-chave e categoria
- Tavily — busca web para produtos em alta em plataformas específicas
- AliExpress Affiliate API — bestsellers por categoria (requer ALIEXPRESS_APP_KEY)
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ── Google Trends ─────────────────────────────────────────────────────────────

def get_google_trends(keywords: str, geo: str = "US", timeframe: str = "today 3-m") -> str:
    """
    Busca tendências no Google Trends para uma ou mais palavras-chave.

    Args:
        keywords: Palavras-chave separadas por vírgula. Ex: "wireless earbuds, led lights, yoga mat"
        geo: Código do país. Ex: "US" (EUA), "BR" (Brasil), "GB" (Reino Unido)
        timeframe: Período. Opções: "now 1-d", "now 7-d", "today 1-m", "today 3-m", "today 12-m"

    Returns:
        str: Relatório com interesse ao longo do tempo e queries relacionadas
    """
    try:
        from pytrends.request import TrendReq

        kw_list = [k.strip() for k in keywords.split(",")][:5]  # máximo 5 keywords

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        pytrends.build_payload(kw_list, geo=geo, timeframe=timeframe)

        # Interesse ao longo do tempo
        interest_df = pytrends.interest_over_time()
        related_queries = pytrends.related_queries()

        lines = [f"## Google Trends — {', '.join(kw_list)} ({geo})\n"]

        if not interest_df.empty:
            # Média de interesse de cada keyword
            lines.append("### Interesse médio no período (0–100)")
            for kw in kw_list:
                if kw in interest_df.columns:
                    avg = round(interest_df[kw].mean(), 1)
                    peak = round(interest_df[kw].max(), 1)
                    lines.append(f"- **{kw}**: média {avg}/100, pico {peak}/100")

        lines.append("\n### Queries relacionadas em alta")
        for kw in kw_list:
            if kw in related_queries and related_queries[kw].get("rising") is not None:
                rising = related_queries[kw]["rising"]
                if not rising.empty:
                    lines.append(f"\n**{kw}:**")
                    for _, row in rising.head(5).iterrows():
                        lines.append(f"  - {row['query']} (+{row['value']}%)")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao buscar Google Trends: {str(e)}"


def get_trending_categories_by_region(geo: str = "US") -> str:
    """
    Retorna as categorias de produtos mais pesquisadas no Google Trends por região.

    Args:
        geo: Código do país. Ex: "US", "BR", "GB", "AU"

    Returns:
        str: Lista de categorias em alta com nível de interesse
    """
    try:
        from pytrends.request import TrendReq

        # Categorias de e-commerce relevantes para o nicho
        categories = [
            "aliexpress finds",
            "shein haul",
            "amazon finds",
            "temu products",
            "cheap gadgets",
        ]

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        pytrends.build_payload(categories, geo=geo, timeframe="today 1-m")

        interest_df = pytrends.interest_over_time()

        lines = [f"## Categorias em alta no Google Trends ({geo}) — últimos 30 dias\n"]

        if not interest_df.empty:
            scores = {}
            for cat in categories:
                if cat in interest_df.columns:
                    scores[cat] = round(interest_df[cat].mean(), 1)

            for cat, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score / 10)
                lines.append(f"- **{cat}**: {score}/100 {bar}")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao buscar categorias: {str(e)}"


# ── Tavily — Pesquisa de produtos em alta ─────────────────────────────────────

def search_trending_products(platform: str, category: str, market: str = "US") -> str:
    """
    Pesquisa produtos em alta em uma plataforma específica usando busca na web.

    Args:
        platform: Plataforma a pesquisar. Opções: "shein", "aliexpress", "amazon", "temu"
        category: Categoria do produto. Ex: "fitness", "home decor", "electronics", "beauty", "fashion"
        market: Mercado alvo. Ex: "US", "Brazil", "UK"

    Returns:
        str: Lista de produtos em alta com preços, tendências e potencial de conteúdo
    """
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        query = f"trending {category} products {platform} {market} 2026 best sellers viral tiktok"

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_answer=True,
        )

        lines = [f"## Produtos em alta — {platform.title()} | {category} | Mercado: {market}\n"]

        if results.get("answer"):
            lines.append(f"### Resumo\n{results['answer']}\n")

        lines.append("### Fontes e resultados")
        for r in results.get("results", []):
            lines.append(f"\n**{r.get('title', '')}**")
            lines.append(f"{r.get('content', '')[:300]}...")
            lines.append(f"[{r.get('url', '')}]({r.get('url', '')})")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao pesquisar produtos em alta: {str(e)}"


def search_viral_products_tiktok(niche: str, market: str = "US") -> str:
    """
    Pesquisa produtos que estão viralizando no TikTok em um nicho específico.

    Args:
        niche: Nicho a pesquisar. Ex: "gym", "skincare", "kitchen", "pet", "home office"
        market: Mercado alvo. Ex: "US", "Brazil", "UK"

    Returns:
        str: Produtos virais com gatilhos, hooks sugeridos e potencial de engajamento
    """
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        query = f"viral tiktok products {niche} {market} 2026 #TikTokMadeMeBuyIt ugc review"

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_answer=True,
        )

        lines = [f"## Produtos virais no TikTok — Nicho: {niche} | Mercado: {market}\n"]

        if results.get("answer"):
            lines.append(f"### Resumo\n{results['answer']}\n")

        lines.append("### Produtos encontrados")
        for r in results.get("results", []):
            lines.append(f"\n**{r.get('title', '')}**")
            lines.append(f"{r.get('content', '')[:400]}...")
            lines.append(f"Fonte: [{r.get('url', '')}]({r.get('url', '')})")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao pesquisar produtos virais: {str(e)}"


def compare_product_prices(product_name: str) -> str:
    """
    Compara preços de um produto entre AliExpress, Amazon, Shein e marcas originais.
    Útil para criar o ângulo 'marca cara vs. produto chinês barato'.

    Args:
        product_name: Nome do produto a comparar. Ex: "wireless earbuds", "led strip lights", "yoga mat"

    Returns:
        str: Comparativo de preços e ângulos de conteúdo sugeridos
    """
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        query = f"{product_name} price comparison aliexpress amazon brand dupe 2026"

        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=6,
            include_answer=True,
        )

        lines = [f"## Comparativo de preços — {product_name}\n"]

        if results.get("answer"):
            lines.append(f"### Resumo\n{results['answer']}\n")

        lines.append("### Referências de preço encontradas")
        for r in results.get("results", []):
            lines.append(f"\n**{r.get('title', '')}**")
            lines.append(f"{r.get('content', '')[:300]}...")

        lines.append("\n### Ângulos de conteúdo sugeridos")
        lines.append(f"- 'I paid $X for {product_name} on AliExpress instead of $Y at [brand]'")
        lines.append(f"- '{product_name} dupe vs. original — honest review'")
        lines.append(f"- 'Stop paying $Y for {product_name} when this exists'")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao comparar preços: {str(e)}"


# ── AliExpress API (opcional) ─────────────────────────────────────────────────

def get_aliexpress_hot_products(category_id: str = "0", keywords: str = "") -> str:
    """
    Busca produtos mais vendidos no AliExpress via API oficial.
    Requer ALIEXPRESS_APP_KEY e ALIEXPRESS_APP_SECRET no .env.

    Args:
        category_id: ID da categoria AliExpress. "0" = todas as categorias.
                     Exemplos: "200003484" (Sports), "200003498" (Beauty), "200003501" (Electronics)
        keywords: Palavras-chave para filtrar produtos. Ex: "wireless", "led", "gym"

    Returns:
        str: Lista de produtos mais vendidos com preços e links
    """
    app_key = os.getenv("ALIEXPRESS_APP_KEY")
    app_secret = os.getenv("ALIEXPRESS_APP_SECRET")

    if not app_key or not app_secret:
        return (
            "AliExpress API não configurada.\n"
            "Para ativar:\n"
            "1. Cadastre-se em https://portals.aliexpress.com\n"
            "2. Crie um app e obtenha APP_KEY e APP_SECRET\n"
            "3. Adicione ao .env: ALIEXPRESS_APP_KEY e ALIEXPRESS_APP_SECRET\n\n"
            "Por enquanto, use search_trending_products('aliexpress', ...) para pesquisar via web."
        )

    try:
        import hashlib
        import hmac
        import time
        import urllib.parse
        import httpx

        timestamp = str(int(time.time() * 1000))
        method = "aliexpress.affiliate.hotproduct.query"

        params = {
            "app_key": app_key,
            "timestamp": timestamp,
            "sign_method": "hmac",
            "method": method,
            "v": "2.0",
            "category_ids": category_id,
            "keywords": keywords,
            "page_no": "1",
            "page_size": "20",
            "sort": "LAST_VOLUME_DESC",
        }

        # Gera assinatura HMAC
        sorted_params = sorted(params.items())
        sign_str = app_secret + "".join(f"{k}{v}" for k, v in sorted_params) + app_secret
        signature = hmac.new(
            app_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()
        params["sign"] = signature

        resp = httpx.get("https://api.aliexpress.com/sync", params=params, timeout=15)
        data = resp.json()

        products = (
            data.get("aliexpress_affiliate_hotproduct_query_response", {})
            .get("resp_result", {})
            .get("result", {})
            .get("products", {})
            .get("product", [])
        )

        if not products:
            return "Nenhum produto encontrado. Tente outros parâmetros."

        lines = [f"## AliExpress Hot Products — categoria: {category_id} | keywords: {keywords}\n"]
        for p in products[:15]:
            title = p.get("product_title", "")[:80]
            price = p.get("target_sale_price", "?")
            original = p.get("target_original_price", "?")
            orders = p.get("lastest_volume", "?")
            url = p.get("promotion_link", p.get("product_detail_url", ""))
            lines.append(f"- **{title}**")
            lines.append(f"  Preço: ${price} (original: ${original}) | Pedidos recentes: {orders}")
            lines.append(f"  {url}\n")

        return "\n".join(lines)

    except Exception as e:
        return f"Erro ao buscar produtos AliExpress: {str(e)}"
