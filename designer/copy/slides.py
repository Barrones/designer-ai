"""
Slide Content Generator — Designer AI v5
Gera conteúdo para slides internos do carrossel com alternância dark/light.

Suporta 5, 7, 9 ou 12 slides com 4 arcos narrativos diferentes.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

from designer.brand.profile import BrandProfile
from designer.copy.headlines import CopyResult
from designer import config


@dataclass
class SlideContent:
    number: int          # posição no carrossel (1-12)
    type: str            # "capa" | "hook" | "contexto" | "mecanismo" | "prova" | "expansao" | "aplicacao" | "direcao" | "cta"
    theme: str           # "dark" | "light" | "gradient" | "capa"
    tag: str             # label acima do conteúdo (ex: "O FENÔMENO")
    headline: str        # headline do slide (UPPERCASE, específica)
    body: str            # texto principal (parágrafo jornalístico)
    body2: str = ""      # segundo bloco opcional
    has_image: bool = False


# ============================================================
# SYSTEM PROMPT
# ============================================================
_SYSTEM = """\
Você é um jornalista sênior da Designer AI, especializado em carrosséis virais para Instagram.

REGRAS DE COPY:
1. Cada slide = 1 ideia — nunca 2
2. Dados específicos com fonte — nunca "muitos profissionais"
3. Tom jornalístico — como Estadão ou InfoMoney
4. Progressão narrativa — cada slide puxa pro próximo
5. Artigos SEMPRE presentes — nunca omitir um/uma/o/a
6. Conectivos naturais — porque, só que, por isso, enquanto, quando, mas
7. Palavras de destaque marcadas com **negrito**

ANTI-AI SLOP (tolerância zero):
- Zero "Não é X, é Y" / "Sem X. Sem Y."
- Zero "E isso muda tudo" / "No fim das contas"
- Zero "Você precisa" / "Devemos" — tom de reportagem
- Zero texto picotado sem conectivos
- Zero headlines genéricas que funcionam com qualquer tema

HEADLINES INTERNAS (slides 2-8):
NÃO são slogans motivacionais. São frases concretas e ancoradas.
❌ "Apareça antes do mainstream" — conselho genérico
❌ "Tema aberto. Posição sua." — slogan vazio
❌ "A virada que ninguém esperava" — genérico
✅ "200 clubes em São Paulo. 3 modelos de negócio." — número + tensão
✅ "O que a Nike entendeu antes de todo mundo" — nome + revelação
✅ "A conta que não fecha: 109% de crescimento, zero retenção" — dado + contradição

SLIDE GRADIENT (penúltimo):
Headline = FRASE DE IMPACTO curta (2-4 palavras), não conselho.
Ex: "Identidade ou extinção." ou "3 sinais. 1 ano."

FECHAMENTO (textos do último slide de conteúdo):
Faz pivot genuíno — NÃO resume o carrossel.
❌ "Em algum escritório do Brasil, alguém está..."
❌ "A pergunta que fica é..."
✅ "Os 1.168 posts provam que distribuição vem primeiro."

CTA:
- Frase-ponte OBRIGATÓRIA conectando conteúdo ao CTA
- Diretivo, sem agradecimento
- "Comenta X, recebe Y"

SEMPRE retorne JSON válido — sem texto extra, sem markdown.
"""


# ============================================================
# GENERATE — new Designer AI system
# ============================================================
def generate_carousel_slides(
    topic: str,
    brand: BrandProfile,
    headline: str,
    espinha_dorsal: dict | None = None,
    n_slides: int = 9,
    carousel_type: str = "tendencia",
    cta_text: str = "",
    n_image_slides: int = 1,
) -> list[SlideContent]:
    """
    Generate all slide content for a Designer AI carousel.

    Parameters
    ----------
    topic           : tema do carrossel
    brand           : perfil da marca
    headline        : headline completa escolhida
    espinha_dorsal  : dict com hook, mecanismo, prova, aplicacao, direcao
    n_slides        : 5, 7, 9 ou 12
    carousel_type   : tendencia | tese | case | previsao
    cta_text        : texto do CTA (ex: "Comenta GUIA")
    n_image_slides  : quantos slides terão imagem
    """
    client = Anthropic()

    # Get slide sequence for this count
    sequence = config.SLIDE_SEQUENCES.get(n_slides, config.SLIDE_SEQUENCES[9])
    arc = config.CAROUSEL_ARCS.get(carousel_type, config.CAROUSEL_ARCS["tendencia"])

    # Build espinha dorsal context
    spine_ctx = ""
    if espinha_dorsal:
        spine_ctx = f"""
ESPINHA DORSAL APROVADA:
- Hook: {espinha_dorsal.get('hook', '')}
- Mecanismo: {espinha_dorsal.get('mecanismo', '')}
- Prova: {espinha_dorsal.get('prova', '')}
- Aplicação: {espinha_dorsal.get('aplicacao', '')}
- Direção: {espinha_dorsal.get('direcao', '')}
"""

    # Build slide structure for prompt
    slides_structure = []
    for i, s in enumerate(sequence):
        if s["type"] == "capa":
            continue  # capa is handled separately
        slides_structure.append(
            f"Slide {i+1} ({s['type']}, {s['theme']})"
        )

    prompt = f"""
TEMA: {topic}
MARCA: {brand.client_name} | NICHO: {brand.subniche}
TOM: {brand.tone}
PÚBLICO: {brand.audience.description}
HEADLINE ESCOLHIDA: {headline}
ARCO NARRATIVO: {arc}
CTA: {cta_text or "Comenta a palavra-chave"}
{spine_ctx}

ESTRUTURA DO CARROSSEL ({n_slides} slides, template alternado claro/escuro):

{chr(10).join(slides_structure)}

Gere o conteúdo para TODOS os slides internos (exceto a capa, que já tem a headline).

Para CADA slide, retorne:
- number: posição (1-{n_slides})
- type: tipo conforme a estrutura acima
- theme: "dark" | "light" | "gradient"
- tag: label curto (ex: "O FENÔMENO", "OS NÚMEROS", "NA PRÁTICA")
- headline: título do slide (CAIXA ALTA, específico, nunca genérico — máx 8 palavras)
- body: texto principal (parágrafo jornalístico com conectivos, 25-40 palavras)
- body2: segundo bloco se necessário (20-30 palavras, opcional — use "" se não precisar)

REGRAS ESPECIAIS:
- Slide de PROVA deve ter dados concretos (números, fontes, anos)
- Slide GRADIENT: headline = frase de impacto curta (2-4 palavras)
- Slide CTA: body = frase-ponte, headline = chamada principal, body2 = benefício, tag = palavra-chave do CTA
- Headlines nunca genéricas — se trocar o tema e a headline ainda funciona, está ruim
- Cada slide deve criar tensão para o próximo (sem "swipe" ou "continue")

Retorne SOMENTE JSON (array de objetos):
[
  {{
    "number": 2,
    "type": "hook",
    "theme": "dark",
    "tag": "O PROBLEMA",
    "headline": "HEADLINE ESPECÍFICA AQUI",
    "body": "Parágrafo jornalístico com conectivos naturais e dados específicos.",
    "body2": ""
  }},
  ...mais slides...
]
"""

    # ---------- CHAMADA CLAUDE COM RETRY ----------
    MAX_RETRIES = 3
    data = None
    last_error = None

    for attempt in range(MAX_RETRIES):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        # Extrair só o array JSON (ignora texto antes/depois)
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start : end + 1]

        # Limpar problemas comuns de JSON
        raw = re.sub(r",\s*([}\]])", r"\1", raw)  # trailing commas
        raw = re.sub(r"[\x00-\x1f]+", " ", raw)   # control chars
        # Aspas simples em valores (ex: l'homme → l\'homme)
        # Substituir newlines literais dentro de strings
        raw = raw.replace("\n", "\\n").replace("\r", "")
        # Mas restaurar newlines reais entre objetos JSON
        raw = raw.replace("\\n  ", "\n  ").replace("\\n]", "\n]").replace("\\n[", "\n[").replace("\\n{", "\n{").replace("\\n}", "\n}")

        try:
            data = json.loads(raw)
            break  # sucesso!
        except json.JSONDecodeError as e:
            last_error = e
            print(f"  ⚠️ Slides JSON parse falhou (tentativa {attempt + 1}/{MAX_RETRIES}): {e}")
            # Salvar raw para debug
            debug_path = f"/tmp/slides_debug_attempt{attempt + 1}.json"
            with open(debug_path, "w") as dbg:
                dbg.write(raw)
            print(f"     Raw salvo em: {debug_path}")

    if data is None:
        raise ValueError(f"Falha ao gerar slides após {MAX_RETRIES} tentativas. Último erro: {last_error}")

    # Build complete slide list (including capa placeholder)
    slides = []

    # Capa (slide 1)
    slides.append(SlideContent(
        number=1,
        type="capa",
        theme="capa",
        tag="",
        headline=headline,
        body="",
        has_image=True,
    ))

    # Internal slides from Claude
    for d in data:
        slide_num = d["number"]
        # Determine if this slide should have an image
        has_img = False
        if n_image_slides > 1 and slide_num in _suggest_image_slides(n_slides, n_image_slides):
            has_img = True

        slides.append(SlideContent(
            number=slide_num,
            type=d["type"],
            theme=d["theme"],
            tag=d.get("tag", "").upper(),
            headline=d.get("headline", "").upper(),
            body=d.get("body", ""),
            body2=d.get("body2", ""),
            has_image=has_img,
        ))

    return slides


def _suggest_image_slides(n_slides: int, n_images: int) -> list[int]:
    """Suggest which slides should have images (besides capa)."""
    # Prioritize dark slides for background images
    if n_slides == 9:
        candidates = [4, 6, 2, 8]  # dark slides first, then gradient
    elif n_slides == 7:
        candidates = [4, 2, 6]
    elif n_slides == 5:
        candidates = [2, 4]
    elif n_slides == 12:
        candidates = [4, 6, 8, 10, 2]
    else:
        candidates = list(range(2, n_slides))

    # Return up to n_images-1 (capa already counts as 1)
    return candidates[:max(0, n_images - 1)]


# ============================================================
# BACKWARD COMPATIBLE — old generate_slides()
# ============================================================
def generate_slides(
    topic: str,
    brand: BrandProfile,
    copy: CopyResult,
    n_content: int = 3,
) -> list[SlideContent]:
    """
    Backward compatible function. Generates slides 2-7 using the new engine.
    """
    headline = f"{copy.headline_part1}: {copy.headline_part2}"

    all_slides = generate_carousel_slides(
        topic=topic,
        brand=brand,
        headline=headline,
        n_slides=7,
        carousel_type="tendencia",
    )

    # Return only internal slides (exclude capa)
    return [s for s in all_slides if s.type != "capa"]
