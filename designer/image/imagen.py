"""
Gemini Imagen 4 — gera imagens customizadas de alta resolução para carrosseis.

Modelos disponíveis:
  imagen-4.0-generate-001       → qualidade padrão (recomendado)
  imagen-4.0-ultra-generate-001 → ultra qualidade (mais lento)
  imagen-4.0-fast-generate-001  → rápido e barato

Uso:
    from designer.image.imagen import generate_image
    path = generate_image(image_query="shocked man holding credit card dim light", output_path="output/bg.png")
"""
from __future__ import annotations

import base64
import os

from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

# Dimensões do carrossel Instagram (4:5)
CANVAS_W = 1080
CANVAS_H = 1350

_MODEL = "imagen-4.0-generate-001"


def generate_image(
    image_query: str,
    output_path: str,
    width: int = CANVAS_W,
    height: int = CANVAS_H,
    model: str = _MODEL,
) -> str:
    """
    Gera uma imagem com Imagen 4 e salva em output_path.

    Parameters
    ----------
    image_query : cena descritiva scroll-stop em inglês
    output_path : caminho local para salvar o PNG
    width/height: dimensões de saída (resize após geração)
    model       : modelo Imagen a usar

    Returns
    -------
    Caminho local do arquivo gerado.
    """
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError("Configure GEMINI_API_KEY no .env")

    # Força uso da chave correta ignorando GOOGLE_API_KEY do ambiente
    _old = os.environ.pop("GOOGLE_API_KEY", None)
    client = genai.Client(api_key=api_key)
    if _old:
        os.environ["GOOGLE_API_KEY"] = _old

    # Enriquece o prompt para scroll-stop e uso como fundo de carrossel
    full_prompt = (
        f"{image_query}, "
        "high contrast dramatic lighting, cinematic composition, "
        "dark areas available for white text overlay, "
        "photorealistic, Instagram carousel background, vertical format"
    )

    response = client.models.generate_images(
        model=model,
        prompt=full_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="3:4",
            safety_filter_level="block_low_and_above",
            person_generation="allow_adult",
        ),
    )

    if not response.generated_images:
        raise RuntimeError(f"Imagen 4 não retornou imagem para: {image_query}")

    # Decodifica e salva
    img_bytes = response.generated_images[0].image.image_bytes
    img = Image.open(io.BytesIO(img_bytes))

    # Garante dimensões exatas
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG", optimize=True)

    return output_path


def generate_reel_background(
    video_query: str,
    output_path: str,
) -> str:
    """
    Gera imagem de fundo para Reel (1080×1920, formato 9:16).
    Usado como fallback quando Pexels não encontra vídeo adequado.
    """
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", "")
    _old = os.environ.pop("GOOGLE_API_KEY", None)
    client = genai.Client(api_key=api_key)
    if _old:
        os.environ["GOOGLE_API_KEY"] = _old

    full_prompt = (
        f"{video_query}, "
        "dramatic cinematic lighting, dark moody atmosphere, "
        "dark areas available for white text overlay, "
        "photorealistic, vertical 9:16 format, Instagram Reels background"
    )

    response = client.models.generate_images(
        model=_MODEL,
        prompt=full_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="9:16",
            safety_filter_level="block_low_and_above",
            person_generation="allow_adult",
        ),
    )

    if not response.generated_images:
        raise RuntimeError(f"Imagen 4 não retornou imagem: {video_query}")

    img_bytes = response.generated_images[0].image.image_bytes
    img = Image.open(io.BytesIO(img_bytes))
    img = img.resize((1080, 1920), Image.LANCZOS)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG", optimize=True)

    return output_path
