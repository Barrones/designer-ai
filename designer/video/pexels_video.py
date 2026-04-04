"""
Pexels Video Search — busca vídeo relevante ao tema e baixa localmente.

Claude Vision vê os thumbnails dos vídeos e escolhe o melhor
(mesma lógica da seleção de fotos para o carrossel).
"""
from __future__ import annotations

import base64
import os
import tempfile

import requests
from dotenv import load_dotenv

load_dotenv()


def get_best_video(
    image_query: str,
    topic: str,
    orientation: str = "portrait",   # "portrait" para Reels (9:16)
    min_duration: int = 5,
    max_duration: int = 30,
    tmp_dir: str = "output/videos/tmp",
) -> str:
    """
    Busca vídeos no Pexels, Claude escolhe o melhor visualmente e baixa.

    Parameters
    ----------
    image_query  : frase descritiva da cena ideal (mesmo campo da foto)
    topic        : tema do post — contexto para o Claude escolher
    orientation  : "portrait" (Reels 9:16) ou "landscape"
    min_duration : duração mínima em segundos
    max_duration : duração máxima em segundos
    tmp_dir      : pasta para salvar o vídeo baixado

    Returns
    -------
    Caminho local do arquivo de vídeo (.mp4)
    """
    api_key = os.getenv("PEXELS_API_KEY", "")
    if not api_key:
        raise EnvironmentError("PEXELS_API_KEY não configurada no .env")

    # 1. Busca vídeos
    candidates = _search_pexels_videos(image_query, api_key, orientation, min_duration, max_duration)

    if not candidates:
        # Tenta query mais genérica
        fallback_query = " ".join(image_query.split()[:2])
        candidates = _search_pexels_videos(fallback_query, api_key, orientation, min_duration, max_duration)

    if not candidates:
        raise RuntimeError(f"Nenhum vídeo encontrado para: {image_query}")

    # 2. Claude escolhe o melhor visualmente
    best_idx = _claude_pick_best_video(candidates, image_query, topic)
    best     = candidates[best_idx]

    # 3. Baixa o vídeo
    os.makedirs(tmp_dir, exist_ok=True)
    video_url  = _pick_video_file(best, orientation)
    video_path = os.path.join(tmp_dir, f"pexels_{best['id']}.mp4")

    if not os.path.exists(video_path):
        print(f"\n  Baixando vídeo ({best.get('duration', '?')}s)... ", end="", flush=True)
        _download_file(video_url, video_path)
        print("pronto")

    return video_path


# ---------------------------------------------------------------------------
# Pexels API
# ---------------------------------------------------------------------------

def _search_pexels_videos(
    query: str,
    api_key: str,
    orientation: str,
    min_dur: int,
    max_dur: int,
    per_page: int = 10,
) -> list[dict]:
    """Retorna lista de vídeos do Pexels."""
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            params={
                "query":       query,
                "orientation": orientation,
                "per_page":    per_page,
                "size":        "medium",
            },
            headers={"Authorization": api_key},
            timeout=12,
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        # Filtra por duração
        return [
            v for v in videos
            if min_dur <= v.get("duration", 0) <= max_dur
        ]
    except Exception:
        return []


def _pick_video_file(video: dict, orientation: str) -> str:
    """Escolhe o arquivo de vídeo de melhor qualidade disponível."""
    files = video.get("video_files", [])
    # Prefere HD portrait ou HD se portrait não disponível
    for quality in ["hd", "sd"]:
        for f in files:
            if f.get("quality") == quality:
                if orientation == "portrait" and f.get("height", 0) > f.get("width", 0):
                    return f["link"]
        # Fallback: qualquer arquivo do quality
        for f in files:
            if f.get("quality") == quality:
                return f["link"]
    return files[0]["link"] if files else ""


def _download_file(url: str, path: str) -> None:
    """Baixa um arquivo em streaming."""
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


# ---------------------------------------------------------------------------
# Claude Vision — escolhe o melhor vídeo pelos thumbnails
# ---------------------------------------------------------------------------

def _claude_pick_best_video(
    videos: list[dict],
    image_query: str,
    topic: str,
) -> int:
    """Usa Claude Vision para escolher o vídeo mais adequado."""
    from anthropic import Anthropic
    client = Anthropic()

    content: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Você é um diretor de arte de Instagram especializado em Reels.\n"
                f"Tema do vídeo: \"{topic}\"\n"
                f"Cena visual ideal: \"{image_query}\"\n\n"
                f"Abaixo estão {len(videos)} thumbnails de vídeos numerados de 0 a {len(videos)-1}.\n"
                f"Escolha o que melhor serve como fundo de Reel (9:16):\n"
                f"- Mais relevante ao tema\n"
                f"- Boa composição para sobrepor texto branco\n"
                f"- Preferencialmente com movimento suave e área escura disponível\n\n"
                f"Responda APENAS com o número do vídeo escolhido (ex: 3)."
            ),
        }
    ]

    valid: list[int] = []
    for i, video in enumerate(videos):
        thumb_url = video.get("image", "")
        if not thumb_url:
            continue
        try:
            r = requests.get(thumb_url, timeout=8)
            if r.status_code == 200:
                b64 = base64.standard_b64encode(r.content).decode()
                content.append({"type": "text", "text": f"Vídeo {i}:"})
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
                })
                valid.append(i)
        except Exception:
            continue

    if not valid:
        return 0

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": content}],
        )
        idx = int(resp.content[0].text.strip())
        return idx if idx in valid else valid[0]
    except Exception:
        return valid[0]
