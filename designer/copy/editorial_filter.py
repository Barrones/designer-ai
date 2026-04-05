"""
Editorial Filter — Anti-AI Slop + Quality Validation
Based on Designer AI methodology (1.168 posts analyzed).

Validates all carousel copy before rendering.
Returns quality scores and specific issues per parameter.
Minimum score: 8/10 per parameter to approve.
"""
from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic


# ============================================================
# PROHIBITED PATTERNS — compiled regex for fast matching
# ============================================================

PROHIBITED_PHRASES = [
    r"não é .+?, é .+",
    r"não é sobre .+?, é sobre",
    r"e isso muda tudo",
    r"no fim das contas",
    r"ao final do dia",
    r"a pergunta (que )?fica",
    r"a questão é",
    r"de forma \w+",
    r"cada vez mais",
    r"em um mundo onde",
    r"vivemos em uma era",
    r"é preciso que",
    r"devemos",
    r"você precisa",
    r"você deve",
    r"simplesmente",
    r"basicamente",
    r"^na prática",
    r"a lógica funciona assim",
    r"o mecanismo funciona assim",
    r"o ponto é",
    r"usando as mesmas 24 horas",
]

PROHIBITED_PARALLELISMS = [
    r"\w+ diminui.+\w+ acelera",
    r"enquanto .+ perde.+ ganha",
    r"menos \w+[\.,] mais \w+",
    r"antes: .+\. agora: .+",
    r"sem \w+\. sem \w+",
]

PROHIBITED_HEADLINES = [
    r"quando .+ vira .+",
    r"^a ascensão de",
    r"^o impacto de",
    r"por que .+ está mudando",
    r"o que você precisa saber",
    r"tudo que você precisa saber",
    r"o guia definitivo",
    r".+ mudou para sempre",
    r"^revelamos",
    r"^descobrimos",
    r"^mostramos",
    r"^descubra",
    r"^saiba",
    r"^conheça",
]

PROHIBITED_OPENINGS = [
    r"^hoje vamos falar",
    r"^neste carrossel",
    r"^antes de começar",
    r"^como você provavelmente",
    r"^muitas pessoas perguntam",
    r"^todo mundo já ouviu",
]

PROHIBITED_CLOSINGS = [
    r"continue no próximo slide",
    r"swipe para ver",
    r"mas tem mais",
    r"não para por aí",
    r"espero que tenha gostado",
    r"se tiver dúvidas",
    r"obrigado por acompanhar",
    r"não esqueça de seguir",
    r"se esse conteúdo te ajudou",
]

VAGUE_DATA = [
    r"estudos mostram",
    r"especialistas dizem",
    r"muitas empresas",
    r"a maioria das pessoas",
    r"recentemente",
]

JARGON = {
    "ecossistema": "sistema, mercado, ambiente",
    "sinergia": "integração, colaboração",
    "disruptivo": "que quebra com o padrão",
    "stakeholders": "envolvidos, partes interessadas",
    "mindset": "mentalidade, modo de pensar",
    "storytelling": "narrativa, história",
    "overview": "visão geral, panorama",
}


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class QualityIssue:
    parameter: str
    severity: str       # "critical" | "warning"
    description: str
    location: str
    suggestion: str


@dataclass
class QualityScore:
    parameter: str
    score: int
    issues: list[QualityIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.score >= 8


@dataclass
class EditorialResult:
    scores: list[QualityScore]
    approved: bool
    total_issues: int
    critical_issues: int

    @property
    def summary(self) -> dict:
        return {
            "approved": self.approved,
            "scores": {s.parameter: s.score for s in self.scores},
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
        }


# ============================================================
# PATTERN SCANNING (fast, regex-based)
# ============================================================

def scan_prohibited_phrases(text: str) -> list[str]:
    """Scan text for prohibited AI slop patterns."""
    matches = []
    text_lower = text.lower()
    for pattern in PROHIBITED_PHRASES:
        m = re.search(pattern, text_lower)
        if m:
            matches.append(m.group())
    return matches


def scan_prohibited_parallelisms(text: str) -> list[str]:
    matches = []
    text_lower = text.lower()
    for pattern in PROHIBITED_PARALLELISMS:
        m = re.search(pattern, text_lower)
        if m:
            matches.append(m.group())
    return matches


def scan_prohibited_headlines(text: str) -> list[str]:
    matches = []
    text_lower = text.lower()
    for pattern in PROHIBITED_HEADLINES:
        m = re.search(pattern, text_lower)
        if m:
            matches.append(m.group())
    return matches


def scan_vague_data(text: str) -> list[str]:
    matches = []
    text_lower = text.lower()
    for pattern in VAGUE_DATA:
        if re.search(pattern, text_lower):
            matches.append(re.search(pattern, text_lower).group())
    return matches


def scan_jargon(text: str) -> list[tuple[str, str]]:
    """Returns (jargon_found, suggested_replacement) pairs."""
    matches = []
    text_lower = text.lower()
    for jargon, replacement in JARGON.items():
        if jargon in text_lower:
            matches.append((jargon, replacement))
    return matches


# ============================================================
# QUICK SCAN — fast pre-check before Claude validation
# ============================================================

def quick_scan(texts: list[str]) -> list[QualityIssue]:
    """
    Fast regex-based scan of all text blocks.
    Catches obvious AI slop before sending to Claude for deep validation.
    """
    issues = []

    for i, text in enumerate(texts):
        location = f"texto {i + 1}"

        for match in scan_prohibited_phrases(text):
            issues.append(QualityIssue(
                parameter="ai_slop",
                severity="critical",
                description=f"Construção proibida: '{match}'",
                location=location,
                suggestion="Reescrever sem usar esta construção",
            ))

        for match in scan_prohibited_parallelisms(text):
            issues.append(QualityIssue(
                parameter="ai_slop",
                severity="critical",
                description=f"Paralelismo forçado: '{match}'",
                location=location,
                suggestion="Reescrever em prosa com conector natural",
            ))

        for match in scan_vague_data(text):
            issues.append(QualityIssue(
                parameter="fatos_verificados",
                severity="warning",
                description=f"Dado vago sem fonte: '{match}'",
                location=location,
                suggestion="Nomear a fonte, o estudo ou dar o número específico",
            ))

        for jargon, replacement in scan_jargon(text):
            issues.append(QualityIssue(
                parameter="tom_editorial",
                severity="warning",
                description=f"Jargão '{jargon}' encontrado",
                location=location,
                suggestion=f"Substituir por: {replacement}",
            ))

        if i % 2 == 0:
            text_lower = text.lower()
            for pattern in PROHIBITED_OPENINGS:
                if re.search(pattern, text_lower):
                    issues.append(QualityIssue(
                        parameter="estrutura",
                        severity="critical",
                        description="Abertura proibida detectada",
                        location=location,
                        suggestion="Começar direto no fato, na tensão ou no dado",
                    ))

    return issues


# ============================================================
# DEEP VALIDATION — Claude-based quality scoring
# ============================================================

_VALIDATION_SYSTEM = """\
Você é um editor-chefe sênior treinado na metodologia Designer AI.
Avalie a qualidade editorial de textos de carrossel para Instagram.

Avalie CADA um dos 7 parâmetros com nota de 0 a 10.
Nota mínima para aprovação: 8 em CADA parâmetro.

PARÂMETROS:

1. GRAMÁTICA — artigos presentes, concordância correta, sem fragmentos
   Penalidade: artigo ausente = máx 7

2. FLUIDEZ — parágrafos de reportagem, conectivos naturais, ritmo alternado
   Penalidade: bloco picotado = máx 5

3. AI SLOP — zero estruturas binárias, zero cacoetes, zero jargão corporativo
   Penalidade: estrutura binária = máx 6, cacoete = máx 5

4. FATOS VERIFICADOS — todo número tem fonte verificável
   Penalidade: dado não verificado = máx 6

5. ESTRUTURA — anatomia preservada, promessas cumpridas
   Penalidade: promessa não cumprida = máx 5

6. DENSIDADE — âncoras concretas, nada genérico
   Penalidade: bloco genérico = máx 6

7. TOM EDITORIAL — jornalístico, sem metalinguagem, sem 2ª pessoa
   Penalidade: segunda pessoa = máx 7

RETORNE SOMENTE JSON:
{
  "scores": [
    {"parameter": "gramatica", "score": N, "issues": ["issue 1"]},
    {"parameter": "fluidez", "score": N, "issues": []},
    {"parameter": "ai_slop", "score": N, "issues": []},
    {"parameter": "fatos_verificados", "score": N, "issues": []},
    {"parameter": "estrutura", "score": N, "issues": []},
    {"parameter": "densidade", "score": N, "issues": []},
    {"parameter": "tom_editorial", "score": N, "issues": []}
  ],
  "approved": true/false,
  "rewrite_needed": ["texto 3", "texto 7"]
}
"""


def validate_deep(texts: list[str], headline: str = "") -> EditorialResult:
    """
    Deep editorial validation using Claude.
    Scores all 7 quality parameters.
    """
    client = Anthropic()

    texts_formatted = "\n".join(
        f"texto {i+1}: {t}" for i, t in enumerate(texts)
    )

    prompt = f"""
HEADLINE DO CARROSSEL: {headline}

TEXTOS PARA AVALIAR:
{texts_formatted}

Avalie cada parâmetro com nota 0-10 e liste os problemas encontrados.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_VALIDATION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(m.group()) if m else {}

    scores = []
    total_issues = 0
    critical_issues = 0

    for s in data.get("scores", []):
        issues = []
        for issue_text in s.get("issues", []):
            severity = "critical" if s["score"] < 8 else "warning"
            issues.append(QualityIssue(
                parameter=s["parameter"],
                severity=severity,
                description=issue_text,
                location="geral",
                suggestion="",
            ))
            total_issues += 1
            if severity == "critical":
                critical_issues += 1

        scores.append(QualityScore(
            parameter=s["parameter"],
            score=s["score"],
            issues=issues,
        ))

    approved = all(s.passed for s in scores)

    return EditorialResult(
        scores=scores,
        approved=approved,
        total_issues=total_issues,
        critical_issues=critical_issues,
    )


# ============================================================
# REWRITE — fixes AI slop issues automatically
# ============================================================

_REWRITE_SYSTEM = """\
Você é um editor sênior da Designer AI. Reescreva os textos indicados corrigindo TODOS os problemas.

REGRAS ABSOLUTAS:
1. Zero artigos omitidos
2. Zero estruturas binárias ("não é X, é Y")
3. Zero cacoetes de IA
4. Zero texto picotado — cada bloco = parágrafo com conectivos
5. Zero dados não verificados
6. Zero segunda pessoa ("você", "seu/sua") no corpo dos slides
7. Tom de jornalista da Folha de S.Paulo

Mantenha o sentido original. Melhore a qualidade sem mudar a mensagem.
RETORNE SOMENTE JSON: {"rewritten": {"texto N": "novo texto", ...}}
"""


def rewrite_issues(
    texts: dict[str, str],
    issues: list[QualityIssue],
) -> dict[str, str]:
    """Automatically rewrite text blocks that have quality issues."""
    if not issues:
        return {}

    client = Anthropic()

    issues_by_location: dict[str, list[str]] = {}
    for issue in issues:
        loc = issue.location
        if loc not in issues_by_location:
            issues_by_location[loc] = []
        issues_by_location[loc].append(f"[{issue.parameter}] {issue.description}")

    blocks = []
    for loc, issue_list in issues_by_location.items():
        if loc in texts:
            blocks.append(f"{loc}: {texts[loc]}")
            blocks.append(f"  PROBLEMAS: {'; '.join(issue_list)}")

    prompt = f"""
TEXTOS COM PROBLEMAS:
{chr(10).join(blocks)}

Reescreva APENAS os textos listados, corrigindo todos os problemas indicados.
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_REWRITE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # tenta extrair JSON do meio do texto
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            return {}
        data = json.loads(m.group())

    return data.get("rewritten", {})


# ============================================================
# CONVENIENCE — full pipeline
# ============================================================

def validate_and_fix(
    texts: list[str],
    headline: str = "",
    max_retries: int = 2,
) -> tuple[list[str], EditorialResult]:
    """
    Full editorial pipeline: scan → validate → rewrite if needed.

    Returns (fixed_texts, final_result)
    """
    current_texts = list(texts)

    for attempt in range(max_retries + 1):
        # Quick scan first
        quick_issues = quick_scan(current_texts)

        # Fix critical issues from quick scan before deep validation
        if attempt == 0 and any(i.severity == "critical" for i in quick_issues):
            texts_dict = {f"texto {i+1}": t for i, t in enumerate(current_texts)}
            critical = [i for i in quick_issues if i.severity == "critical"]
            rewritten = rewrite_issues(texts_dict, critical)
            for key, new_text in rewritten.items():
                idx = int(key.split()[-1]) - 1
                if 0 <= idx < len(current_texts):
                    current_texts[idx] = new_text

        # Deep validation
        result = validate_deep(current_texts, headline)

        if result.approved:
            return current_texts, result

        if attempt < max_retries:
            all_issues = []
            for score in result.scores:
                if not score.passed:
                    all_issues.extend(score.issues)

            if all_issues:
                texts_dict = {f"texto {i+1}": t for i, t in enumerate(current_texts)}
                rewritten = rewrite_issues(texts_dict, all_issues)
                for key, new_text in rewritten.items():
                    idx = int(key.split()[-1]) - 1
                    if 0 <= idx < len(current_texts):
                        current_texts[idx] = new_text

    return current_texts, result
