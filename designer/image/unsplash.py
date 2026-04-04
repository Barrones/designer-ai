"""
Busca de imagem contextual.

Prioridade:
  1. Pexels API   (PEXELS_API_KEY no .env) — busca 10 fotos, Claude escolhe a melhor
  2. Unsplash API (UNSPLASH_ACCESS_KEY no .env)
  3. LoremFlickr  (fallback sem auth)
"""
from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def get_image_url(
    image_query: str,
    topic: str = "",
    width: int = 1080,
    height: int = 1350,
) -> str:
    """
    Retorna URL de imagem contextual pronta para o renderer.

    Parameters
    ----------
    image_query : frase descritiva da cena ideal (ex: "man frustrated looking at supplements")
    topic       : tema do post — usado pelo Claude para escolher a melhor foto
    width       : largura desejada
    height      : altura desejada
    """
    # 1. Pexels — busca 10 fotos e escolhe a mais relevante via Claude
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    if pexels_key:
        url = _pexels_best_match(image_query, topic, width, height, pexels_key)
        if url:
            return url

    # 2. Unsplash API oficial
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
    if unsplash_key:
        url = _unsplash_api(image_query, width, height, unsplash_key)
        if url:
            return url

    # 3. LoremFlickr — fallback final
    simple = image_query.split()[:3]
    query = ",".join(simple)
    return f"https://loremflickr.com/{width}/{height}/{query}"


def _pexels_best_match(
    image_query: str,
    topic: str,
    width: int,
    height: int,
    api_key: str,
) -> str | None:
    """Busca 10 fotos no Pexels e usa Claude para escolher a que melhor bate com o tema."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={
                "query": image_query,
                "per_page": 10,
                "orientation": "portrait",
            },
            headers={"Authorization": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            return None

        # Se só 1 foto, retorna direto
        if len(photos) == 1:
            src = photos[0].get("src", {})
            return src.get("portrait") or src.get("large2x")

        # Claude escolhe a melhor entre as opções
        best_idx = _claude_pick_best_photo(photos, image_query, topic)
        src = photos[best_idx].get("src", {})
        return src.get("portrait") or src.get("large2x")

    except Exception:
        pass
    return None


def _claude_pick_best_photo(
    photos: list[dict],
    image_query: str,
    topic: str,
) -> int:
    """Usa Claude Vision para escolher a melhor foto visualmente."""
    import base64
    from anthropic import Anthropic

    client = Anthropic()

    # Baixa thumbnails pequenos para análise visual (tiny = ~280px)
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Você é um diretor de arte de Instagram.\n"
                f"Tema do post: \"{topic}\"\n"
                f"Imagem ideal para o fundo: \"{image_query}\"\n\n"
                f"Abaixo estão {len(photos)} fotos numeradas de 0 a {len(photos)-1}.\n"
                f"Escolha a que melhor serve como FUNDO de carrossel:\n"
                f"- Mais relevante ao tema\n"
                f"- Boa composição para sobrepor texto branco\n"
                f"- Preferencialmente com área escura na parte inferior\n\n"
                f"Responda APENAS com o número da foto escolhida (ex: 3)."
            ),
        }
    ]

    valid_indices: list[int] = []
    for i, photo in enumerate(photos):
        thumb_url = photo.get("src", {}).get("tiny") or photo.get("src", {}).get("small")
        if not thumb_url:
            continue
        try:
            r = requests.get(thumb_url, timeout=8)
            if r.status_code == 200:
                img_b64 = base64.standard_b64encode(r.content).decode()
                content.append({
                    "type": "text",
                    "text": f"Foto {i}:",
                })
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_b64,
                    },
                })
                valid_indices.append(i)
        except Exception:
            continue

    if not valid_indices:
        return 0

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": content}],
        )
        idx = int(response.content[0].text.strip())
        return idx if idx in valid_indices else valid_indices[0]
    except Exception:
        return valid_indices[0]


def _unsplash_api(
    image_query: str,
    width: int,
    height: int,
    access_key: str,
) -> str | None:
    """API oficial do Unsplash — retorna foto mais relevante ou None."""
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": image_query,
                "per_page": 1,
                "orientation": "portrait",
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            raw_url = results[0]["urls"]["raw"]
            return f"{raw_url}&w={width}&h={height}&fit=crop&crop=entropy"
    except Exception:
        pass
    return None
