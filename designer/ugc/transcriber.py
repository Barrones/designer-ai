"""
UGC Transcriber — transcreve vídeos de criadores usando Whisper via Groq.

Uso:
    python -m designer.ugc.transcriber                    # transcreve todos os criadores
    python -m designer.ugc.transcriber --creator nome     # só um criador
    python -m designer.ugc.transcriber --add nome /path   # adiciona criador novo

Estrutura de pastas:
    creator_profiles/
        <creator>/
            videos/    ← coloca os .mp4 aqui
            transcriptions.json  ← gerado automaticamente
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

CREATORS_DIR = Path(__file__).parent.parent.parent / "creator_profiles"


def list_creators() -> list[str]:
    """Lista todos os criadores disponíveis."""
    if not CREATORS_DIR.exists():
        return []
    return [d.name for d in CREATORS_DIR.iterdir() if d.is_dir() and (d / "videos").exists()]


def transcribe_creator(creator: str, force: bool = False) -> dict:
    """
    Transcreve todos os vídeos de um criador.
    Pula vídeos já transcritos (a menos que force=True).
    """
    from groq import Groq

    creator_dir = CREATORS_DIR / creator
    videos_dir  = creator_dir / "videos"
    trans_file  = creator_dir / "transcriptions.json"

    if not videos_dir.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {videos_dir}")

    client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

    # Carrega transcrições existentes
    existing: dict = {}
    if trans_file.exists() and not force:
        existing = json.loads(trans_file.read_text(encoding="utf-8"))

    videos = list(videos_dir.glob("*.mp4"))
    print(f"\n  {creator}: {len(videos)} vídeos encontrados")

    for video in videos:
        if video.name in existing:
            print(f"    → {video.name} (já transcrito)")
            continue

        print(f"    → Transcrevendo {video.name}...", end="", flush=True)
        try:
            audio_path = _extract_audio(str(video))
            text = _transcribe_audio(audio_path, client)
            existing[video.name] = text
            os.unlink(audio_path)
            print(" ok")
        except Exception as e:
            print(f" ERRO: {e}")

    # Salva
    trans_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    ✓ Salvo em {trans_file}")
    return existing


def transcribe_all(force: bool = False) -> None:
    """Transcreve todos os criadores disponíveis."""
    creators = list_creators()
    if not creators:
        print("Nenhum criador encontrado em creator_profiles/")
        return
    for creator in creators:
        transcribe_creator(creator, force=force)


def get_transcriptions(creator: str) -> str:
    """Retorna transcrições de um criador formatadas para o prompt."""
    trans_file = CREATORS_DIR / creator / "transcriptions.json"

    if not trans_file.exists():
        raise FileNotFoundError(f"Transcrições não encontradas para '{creator}'. Rode o transcriber primeiro.")

    data = json.loads(trans_file.read_text(encoding="utf-8"))
    parts = []
    for i, (video, text) in enumerate(data.items(), 1):
        parts.append(f"### Vídeo {i} ({video})\n{text}")

    return f"# Transcrições de @{creator}\n\n" + "\n\n".join(parts)


def get_all_creators_summary() -> str:
    """Lista criadores disponíveis com contagem de vídeos."""
    creators = list_creators()
    if not creators:
        return "Nenhum criador disponível."
    lines = []
    for c in creators:
        trans_file = CREATORS_DIR / c / "transcriptions.json"
        count = 0
        if trans_file.exists():
            count = len(json.loads(trans_file.read_text(encoding="utf-8")))
        videos = len(list((CREATORS_DIR / c / "videos").glob("*.mp4")))
        lines.append(f"  → {c}: {videos} vídeos, {count} transcritos")
    return "Criadores disponíveis:\n" + "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_audio(video_path: str) -> str:
    """Extrai áudio do vídeo como MP3 temporário."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3",
         "-ar", "16000", "-ac", "1", tmp.name, "-y"],
        check=True, capture_output=True,
    )
    return tmp.name


def _transcribe_audio(audio_path: str, client) -> str:
    """Transcreve áudio com Whisper via Groq."""
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            response_format="text",
        )
    return resp


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Transcreve vídeos de criadores")
    parser.add_argument("--creator", help="Criador específico (opcional)")
    parser.add_argument("--force", action="store_true", help="Retranscreve mesmo se já existir")
    parser.add_argument("--list", action="store_true", help="Lista criadores disponíveis")
    args = parser.parse_args()

    if args.list:
        print(get_all_creators_summary())
    elif args.creator:
        transcribe_creator(args.creator, force=args.force)
    else:
        transcribe_all(force=args.force)
