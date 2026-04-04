"""
Multilingual Copy Engine — gera copy em qualquer idioma usando Gemini Flash.

Gemini Flash: barato, rápido, excelente em idiomas europeus e asiáticos.
Claude Vision: mantido para seleção de imagem/vídeo (ponto forte dele).

Uso:
    from designer.copy.multilingual import generate_multilingual
    copy = generate_multilingual(topic="scarpe da corsa", brand=brand, language="it", country="IT")
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Mapeamento país → idioma padrão e contexto de mercado
MARKET_DEFAULTS = {
    "BR": {"language": "pt-BR", "language_name": "Brazilian Portuguese", "currency": "BRL", "platform": "Instagram"},
    "IT": {"language": "it",    "language_name": "Italian",             "currency": "EUR", "platform": "Instagram"},
    "US": {"language": "en",    "language_name": "English",             "currency": "USD", "platform": "Instagram"},
    "ES": {"language": "es",    "language_name": "Spanish",             "currency": "EUR", "platform": "Instagram"},
    "DE": {"language": "de",    "language_name": "German",              "currency": "EUR", "platform": "Instagram"},
    "FR": {"language": "fr",    "language_name": "French",              "currency": "EUR", "platform": "Instagram"},
    "MX": {"language": "es-MX", "language_name": "Mexican Spanish",     "currency": "MXN", "platform": "Instagram"},
    "AR": {"language": "es-AR", "language_name": "Argentine Spanish",   "currency": "ARS", "platform": "Instagram"},
    "PT": {"language": "pt-PT", "language_name": "European Portuguese", "currency": "EUR", "platform": "Instagram"},
    "JP": {"language": "ja",    "language_name": "Japanese",            "currency": "JPY", "platform": "Instagram"},
    "UK": {"language": "en-GB", "language_name": "British English",     "currency": "GBP", "platform": "Instagram"},
}

_FORMULAS = """
F1 — CONTEXT + PROVOCATION
  Structure: "[Context about the topic]: [Provocative statement generating curiosity]"
  Use when: topic involves a known character, brand, or situation.

F2 — BOLD CLAIM + QUESTION
  Structure: "[Direct strong statement]: [Question the audience already asks themselves]"
  Use when: positioning, market trend, future of the niche.

F3 — NEWS + IMPACT DATA
  Structure: "[Fact or niche news] [surprising number]"
  Use when: data, research, launches, trends with numbers.

F4 — PURE PROVOCATION
  Structure: "[Name of problem or trap]: [Counter-intuitive consequence]"
  Use when: common mistakes, myths, self-destructive behaviors.

SPLIT RULE:
  - Part 1 (white text): context, setup, name of the problem — ends with ":" or period
  - Part 2 (accent color): the most provocative part, the twist, the shocking data
  - Both in ALL CAPS in the target language
"""

_SCROLL_STOP_RULES = """
SCROLL-STOP VISUAL PSYCHOLOGY (image_query and video_query ALWAYS in English):

1. VISIBLE EMOTION — prefer faces with strong emotion (shock, relief, anger, euphoria)
   ❌ "person holding credit card"
   ✅ "shocked young man staring at phone screen with credit card in hand, dim light"

2. TENSION OR CONTRAST — create visual conflict (light vs dark, wealth vs poverty)
   ❌ "woman at the gym"
   ✅ "exhausted woman sitting on gym floor head down, single spotlight"

3. IMPLIED MOVEMENT — frame must look like a captured moment, not a pose
   ❌ "businessman smiling"
   ✅ "man running out of bank door looking desperate, motion blur"

4. CLOSE-UP OR UNUSUAL ANGLE
   ❌ "pile of money"
   ✅ "extreme close-up of crumpled bills scattered on dark floor"

5. FOR VIDEO (video_query): prioritize MOVEMENT and ACTION
   ❌ "city buildings"
   ✅ "timelapse of busy city street at night, neon lights reflecting on wet pavement"

GOLDEN RULE: if the scene wouldn't make someone pause their scroll, rewrite it.
"""


@dataclass
class MultilingualCopyResult:
    formula: str
    headline_part1: str     # ALL CAPS in target language
    headline_part2: str     # ALL CAPS in target language
    caption: str            # full caption in target language
    hashtags: list[str]     # localized hashtags
    image_query: str        # scroll-stop scene (always English)
    video_query: str        # scroll-stop video scene (always English)
    language: str           # e.g. "it", "es", "de"
    country: str            # e.g. "IT", "ES", "DE"


def generate_multilingual(
    topic: str,
    brand,
    country: str = "BR",
    language: str | None = None,
) -> MultilingualCopyResult:
    """
    Gera copy completo no idioma do país usando Gemini Flash.

    Parameters
    ----------
    topic    : tema do post
    brand    : BrandProfile
    country  : código do país (BR, IT, US, ES, DE, FR, MX...)
    language : override do idioma (opcional — usa padrão do país se None)
    """
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError("Configure GEMINI_API_KEY no .env")

    genai.configure(api_key=api_key)

    market = MARKET_DEFAULTS.get(country.upper(), MARKET_DEFAULTS["BR"])
    lang   = language or market["language"]
    lang_name = market["language_name"]
    currency  = market["currency"]

    brand_context = f"""
BRAND: {brand.client_name}
NICHE: {brand.subniche}
TONE: {brand.tone}
CONTENT PILLARS: {", ".join(brand.content_pillars)}
AUDIENCE: {brand.audience.description} ({brand.audience.age_range})
AUDIENCE PAINS: {" | ".join(brand.audience.pains)}
HANDLE: {brand.handle or "@" + brand.slug}
TARGET MARKET: {country} — write in {lang_name}
CURRENCY: {currency}
"""

    prompt = f"""You are a senior copywriter and art director specialized in high-impact Instagram content.
You create scroll-stopping content for the {country} market.

TOPIC: {topic}
TARGET LANGUAGE: {lang_name} (ISO: {lang})
BRAND PROFILE:
{brand_context}

HEADLINE FORMULAS:
{_FORMULAS}

VISUAL QUERY RULES:
{_SCROLL_STOP_RULES}

TASK: Generate complete copy for a high-impact Instagram post in {lang_name}.

RULES:
- headline_part1 and headline_part2: ALL CAPS in {lang_name}
- caption: natural, engaging, 3-5 short paragraphs in {lang_name} — ends with question or CTA
- hashtags: mix of niche + behavior + reach tags relevant to {country} market, in {lang_name} and/or English
- image_query: scroll-stopping photo scene — ALWAYS IN ENGLISH — 5 to 10 words
- video_query: scroll-stopping video scene with movement — ALWAYS IN ENGLISH — 5 to 10 words

Return ONLY this JSON (no markdown, no extra text):
{{
  "formula": "F1|F2|F3|F4",
  "headline_part1": "SETUP/CONTEXT IN {lang_name.upper()}",
  "headline_part2": "TWIST/PROVOCATIVE PART IN {lang_name.upper()}",
  "caption": "Full caption in {lang_name}",
  "hashtags": ["#hashtag1", "#hashtag2"],
  "image_query": "scroll-stopping photo scene in english",
  "video_query": "scroll-stopping video scene with movement in english"
}}"""

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw.strip())

    return MultilingualCopyResult(
        formula=data["formula"],
        headline_part1=data["headline_part1"].upper(),
        headline_part2=data["headline_part2"].upper(),
        caption=data["caption"],
        hashtags=data.get("hashtags", []),
        image_query=data.get("image_query", topic),
        video_query=data.get("video_query", data.get("image_query", topic)),
        language=lang,
        country=country.upper(),
    )
