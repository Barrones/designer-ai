"""
Figma Export — formata o output do Designer AI para o plugin Figma.

O plugin espera:
  - Textos no formato: "texto 1 - conteúdo\ntexto 2 - conteúdo\n..."
  - Cores como array de 3 hex: [light_bg, accent, dark_bg]
  - Perfil: handle (@), nome, avatar

Estrutura de layers no Figma:
  - "texto N" → camadas de texto nos slides
  - "imagem N" → camadas de imagem
  - "Perfil" → @handle
  - "Nome" → nome da marca
  - "Foto Perfil" → avatar/logo
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from designer.copy.slides import SlideContent


@dataclass
class FigmaPayload:
    """Payload formatado para o plugin Figma."""
    texts: str              # "texto 1 - ...\ntexto 2 - ..."
    colors: list[str]       # ["#F5F2EF", "#E8421A", "#0F0D0C"]
    handle: str             # "@designerai"
    name: str               # "Designer AI"
    text_count: int         # total de textos
    slide_count: int        # total de slides


def format_for_figma(
    slides: list[SlideContent],
    palette: dict,
    handle: str = "",
    brand_name: str = "",
) -> FigmaPayload:
    """
    Converte os slides do Designer AI para o formato do plugin Figma.

    Mapping (9 slides padrão = 18 textos):
      Slide 1 (Capa):     texto 1 = tag/chapéu, texto 2 = headline
      Slide 2 (Hook):     texto 3 = body, texto 4 = body2
      Slide 3 (Contexto): texto 5 = body, texto 6 = body2
      Slide 4 (Mecanismo):texto 7 = body, texto 8 = body2
      Slide 5 (Prova):    texto 9 = body, texto 10 = body2
      Slide 6 (Expansão): texto 11 = body, texto 12 = body2
      Slide 7 (Aplicação): texto 13 = body, texto 14 = body2
      Slide 8 (Direção):  texto 15 = body, texto 16 = body2
      Slide 9 (CTA):      texto 17 = body (bridge), texto 18 = body2 (benefit)
    """
    lines = []
    text_num = 1

    for slide in slides:
        if slide.type == "capa":
            # Capa: texto 1 = tag, texto 2 = headline
            lines.append(f"texto {text_num} - {slide.tag or slide.type.upper()}")
            text_num += 1
            lines.append(f"texto {text_num} - {slide.headline}")
            text_num += 1
        else:
            # Slides internos: texto N = body, texto N+1 = body2 ou headline
            if slide.headline and slide.body:
                # Se tem headline E body, headline vai no texto ímpar, body no par
                lines.append(f"texto {text_num} - {slide.headline}")
                text_num += 1
                lines.append(f"texto {text_num} - {slide.body}")
                text_num += 1
            elif slide.body:
                lines.append(f"texto {text_num} - {slide.body}")
                text_num += 1
                if slide.body2:
                    lines.append(f"texto {text_num} - {slide.body2}")
                else:
                    lines.append(f"texto {text_num} - ")
                text_num += 1
            else:
                lines.append(f"texto {text_num} - {slide.headline or ''}")
                text_num += 1
                lines.append(f"texto {text_num} - {slide.body2 or ''}")
                text_num += 1

    texts_formatted = "\n".join(lines)

    # Cores: [light_bg, accent/primary, dark_bg]
    colors = [
        palette.get("light_bg_hex", "#F5F2EF"),
        palette.get("primary_hex", "#E8421A"),
        palette.get("dark_bg_hex", "#0F0D0C"),
    ]

    return FigmaPayload(
        texts=texts_formatted,
        colors=colors,
        handle=handle,
        name=brand_name,
        text_count=text_num - 1,
        slide_count=len(slides),
    )


def print_figma_output(payload: FigmaPayload) -> str:
    """
    Retorna o output formatado pra o usuário copiar e colar no plugin Figma.
    """
    output = []
    output.append("=" * 60)
    output.append("  DESIGNER AI → FIGMA PLUGIN")
    output.append("=" * 60)

    output.append("\n📝 TEXTOS (copiar e colar no campo 'Textos' do plugin):")
    output.append("-" * 60)
    output.append(payload.texts)

    output.append("\n🎨 CORES (selecionar ou criar paleta no plugin):")
    output.append("-" * 60)
    output.append(f"  Cor 1 (fundo claro): {payload.colors[0]}")
    output.append(f"  Cor 2 (accent):      {payload.colors[1]}")
    output.append(f"  Cor 3 (fundo escuro): {payload.colors[2]}")

    output.append(f"\n👤 PERFIL:")
    output.append("-" * 60)
    output.append(f"  Handle: {payload.handle}")
    output.append(f"  Nome:   {payload.name}")

    output.append(f"\n📊 Resumo: {payload.text_count} textos · {payload.slide_count} slides · 3 cores")
    output.append("=" * 60)

    return "\n".join(output)
