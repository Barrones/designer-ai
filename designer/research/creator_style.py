"""
Creator Style Extractor
Lê transcrições do Agente de IA e extrai o DNA de estilo do criador via Claude.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from anthropic import Anthropic

# Caminho para o projeto Agente de IA
_AGENTE_DIR = Path(__file__).parents[3] / "Agente de IA para criação de conteúdo"
_TRANSCRIPTIONS_PATH = _AGENTE_DIR / "transcriptions.json"


@dataclass
class CreatorStyle:
    creator: str
    hook_patterns: list[str]         # Como o criador abre cada vídeo
    sentence_style: str              # Curto/direto, narrativo, técnico etc.
    vocabulary: list[str]            # Palavras e expressões características
    tone: str                        # Tom: energético, calmo, autoridade, etc.
    structure: str                   # Como organiza o conteúdo (cliffhanger, lista, etc.)
    cta_style: str                   # Como pede a ação (se pede)
    raw_summary: str                 # Resumo completo em prosa


def list_creators() -> list[str]:
    """Retorna lista de criadores disponíveis nas transcrições."""
    if not _TRANSCRIPTIONS_PATH.exists():
        return []
    with open(_TRANSCRIPTIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return list(data.keys())


def _load_transcriptions(creator: str) -> list[str]:
    """Carrega todas as transcrições de um criador."""
    if not _TRANSCRIPTIONS_PATH.exists():
        raise FileNotFoundError(f"transcriptions.json não encontrado em {_TRANSCRIPTIONS_PATH}")
    with open(_TRANSCRIPTIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if creator not in data:
        raise ValueError(f"Criador '{creator}' não encontrado. Disponíveis: {list(data.keys())}")
    return [entry["transcription"] for entry in data[creator] if entry.get("transcription")]


def extract_creator_style(creator: str) -> CreatorStyle:
    """
    Usa Claude para extrair o DNA de estilo de um criador a partir de suas transcrições.
    """
    transcriptions = _load_transcriptions(creator)
    # Usa até 8 transcrições para não exceder contexto
    sample = transcriptions[:8]
    joined = "\n\n---\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(sample))

    client = Anthropic()

    system = """\
Você é um analista de conteúdo e copywriter sênior especialista em UGC (User Generated Content).
Sua tarefa é analisar transcrições de vídeos e extrair o DNA de estilo do criador.
Retorne APENAS JSON válido, sem texto extra, sem markdown.
"""

    prompt = f"""Analise as transcrições abaixo do criador "{creator}" e extraia o DNA de estilo.

TRANSCRIÇÕES:
{joined}

Extraia:
1. hook_patterns — como o criador abre seus vídeos (liste os padrões que se repetem)
2. sentence_style — describe em 1 frase o estilo das frases (curtas/diretas? narrativas? técnicas?)
3. vocabulary — palavras, expressões ou frases características que o criador usa com frequência
4. tone — tom emocional dominante (ex: entusiasta, autoritativo, casual, urgente)
5. structure — como o conteúdo é estruturado (ex: problema → solução, lista numerada, storytelling)
6. cta_style — como o criador pede ação (ex: "tap now", "clica aqui", implícito sem CTA direto)
7. raw_summary — 2-3 frases descrevendo o estilo geral para um copywriter usar como referência

Retorne:
{{
  "hook_patterns": ["padrão 1", "padrão 2", "padrão 3"],
  "sentence_style": "descrição do estilo",
  "vocabulary": ["palavra1", "expressão2", "frase3"],
  "tone": "tom dominante",
  "structure": "como estrutura o conteúdo",
  "cta_style": "como pede ação",
  "raw_summary": "resumo em prosa para o copywriter"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw.strip())

    return CreatorStyle(
        creator=creator,
        hook_patterns=data.get("hook_patterns", []),
        sentence_style=data.get("sentence_style", ""),
        vocabulary=data.get("vocabulary", []),
        tone=data.get("tone", ""),
        structure=data.get("structure", ""),
        cta_style=data.get("cta_style", ""),
        raw_summary=data.get("raw_summary", ""),
    )


def style_to_prompt_block(style: CreatorStyle) -> str:
    """Formata o CreatorStyle em bloco de texto para injetar no prompt de copy."""
    hooks = "\n".join(f"  - {h}" for h in style.hook_patterns[:5])
    vocab = ", ".join(style.vocabulary[:10])
    return f"""
━━━ ESTILO DO CRIADOR DE REFERÊNCIA: {style.creator.upper()} ━━━

Você deve escrever a legenda e o hook inspirado no estilo deste criador — não copie,
adapte a voz para o nicho da marca mantendo a essência do estilo.

PADRÕES DE ABERTURA (hook):
{hooks}

ESTILO DE FRASE: {style.sentence_style}
TOM: {style.tone}
ESTRUTURA PREFERIDA: {style.structure}
VOCABULÁRIO CARACTERÍSTICO: {vocab}
CTA PREFERIDO: {style.cta_style}

RESUMO PARA O COPYWRITER:
{style.raw_summary}

INSTRUÇÃO: Use esses padrões para escrever a legenda com a voz do criador,
mas adaptada ao nicho e compliance da marca.
"""
