"""
Copy Engine — Designer AI Headline Engine v5
Gera 10 headlines calibradas por dados de 1.168 posts analisados.
Inclui lift patterns, gatilhos emocionais e checklist de rejeição.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from anthropic import Anthropic
from designer.brand.profile import BrandProfile


# ============================================================
# HEADLINE FORMATS
# ============================================================
_HEADLINE_FORMATS = """
FORMATO 1 — INVESTIGAÇÃO CULTURAL (opções 1–5)
Estrutura OBRIGATÓRIA: [Reenquadramento provocativo]: [Hook de curiosidade]
Separadas por dois-pontos. Frase 1 redefine o fenômeno. Frase 2 cria lacuna.

Exemplos CORRETOS (banco de 56 hooks com +10k likes):
- "A Morte do Gosto Pessoal: Como a Dopamina Digital Nos Tornou Indiferentes" (115k likes)
- "A corrida virou a nova balada: por que a Geração Z trocou o bar pelo asfalto às 6h da manhã"
- "O dado que nenhum guru quer admitir: posts sobre o nicho performam 4× pior que posts sobre cultura"
- "A Morte dos Influencers de Lifestyle: Bem-vindos à Nova Era da Criação de Conteúdo" (82k likes)
- "O Fim do Conteúdo Fast Food: Por que Posts Inteligentes estão Voltando a Dominar o Instagram" (17k likes)

Exemplos ERRADOS (rejeitar imediatamente):
- ❌ "As academias reabriram. Ninguém parou de correr." — falta dois-pontos, falta hook de curiosidade
- ❌ "A corrida é o novo fenômeno do Brasil" — declaração direta, sem tensão
- ❌ "Por que todo mundo está correndo" — pergunta genérica sem reenquadramento

Os 5 subpadrões de IC com maior performance:
IC-1 (Morte/Fim): "A Morte de [X]: [Revelação]" — média 57k likes
IC-2 (Geracional): "Por que [Geração] está [Comportamento Inesperado]?" — média 28k likes
IC-3 (Investigando): "Investigando [Fenômeno]" — média 18k likes
IC-4 (Pop + Revelação): "Como [Nome/Marca] [Ação Inesperada]" — média 20k likes
IC-5 (Contraste): dois elementos opostos em tensão — média 22k likes

FORMATO 2 — NARRATIVA MAGNÉTICA (opções 6–10)
Estrutura OBRIGATÓRIA: [Cenário concreto]. [Mecanismo]. [Tensão aberta]
EXATAMENTE 3 frases com ponto. Frase 1 descreve o que aconteceu. Frase 2 explica como funciona. Frase 3 abre tensão.

Exemplos CORRETOS:
- "Padre Reginaldo faz live de oração todo dia às 4h da manhã. Tem mais audiência simultânea que streamer profissional, final de campeonato, lançamento de série. Não viralizou, criou rotina — pessoas acordam pra isso."
- "A Hoka triplicou o faturamento no Brasil três anos seguidos. Nenhum influenciador de lifestyle recomendou. O boca a boca saiu dos clubes de corrida."
- "Jaden Smith abriu um restaurante onde ninguém paga. O modelo funciona porque cada refeição servida gera R$50 em cobertura de mídia espontânea. Nenhuma agência de publicidade teria criado isso." (53k likes)

Exemplos ERRADOS:
- ❌ "A corrida está mudando o Brasil" — frase única, sem 3 partes
- ❌ "Correr virou tendência entre jovens brasileiros" — genérico, sem cenário concreto
- ❌ Mais de 3 frases — estrutura quebrada

DISTRIBUIÇÃO INTERNA DAS 10:
1. Reenquadramento | 2. Conflito oculto | 3. Implicação sistêmica
4. Contradição | 5. Ameaça ou oportunidade
6. Nomeação | 7. Diagnóstico cultural | 8. Inversão
9. Ambição de mercado | 10. Mecanismo social
"""

# ============================================================
# LIFT PATTERNS
# ============================================================
_LIFT_PATTERNS = """
PADRÕES COM LIFT POSITIVO (usar):
| Padrão | Lift | Quando usar |
|---|---|---|
| Brasil / Contexto Nacional | +155% | Tema conectável com identidade brasileira |
| Fim / Morte / Crise | +119% | Algo mudando, acabando ou em risco |
| Geracional | +119% | Comportamento de Gen Z, Millennials, Boomers |
| Novidade | +99% | Tendência emergente, algo novo |

PADRÕES COM LIFT NEGATIVO (evitar):
| Padrão | Lift |
|---|---|
| Declaração Direta | -29% |
| Revelação Genérica | -42% |
| Lista / Dicas / Número | formato morto |
| Motivacional Vazio | formato morto |

PALAVRAS-GATILHO DE ALTA PERFORMANCE:
morte · novo · fim · brasil · investigando · crise · geração · instagram

6 GATILHOS EMOCIONAIS (mínimo 2 por headline):
- Nostalgia — memória afetiva
- Medo/Alerta — urgência, algo em risco
- Indignação — revolta, "isso está errado"
- Identidade — "isso é sobre mim"
- Curiosidade — lacuna de informação
- Aspiração — desejo de ser/ter/alcançar

COMBINAÇÕES DE ALTA PERFORMANCE:
- Nostalgia + Identidade
- Medo + Geracional
- Brasil + Identidade
- Curiosidade + Nostalgia
"""

# ============================================================
# REJECTION CHECKLIST
# ============================================================
_REJECTION_CHECKLIST = """
CHECKLIST DE REJEIÇÃO (rodar em CADA headline antes de entregar):

Se a headline cair em qualquer um destes, REESCREVER (nunca remover):
❌ Declaração Direta — afirma sem provocar
❌ Revelação Genérica — começa com "descubra", "saiba", "conheça"
❌ Lista / Número de itens — "5 dicas para..."
❌ Motivacional Vazio — sem tensão, sem dado, sem conflito
❌ Tom de IA — qualquer conta poderia ter escrito
❌ Proibidos: "quando X vira Y", "a ascensão de", "o impacto de",
   "por que X está mudando", "não é X, é Y", "virou" como verbo principal

VALIDAÇÃO OBRIGATÓRIA:
- IC (1-5): tem dois-pontos separando reenquadramento de hook? Se NÃO → reescrever
- NM (6-10): tem exatamente 3 frases com ponto? Se NÃO → reescrever
- Tem pelo menos 2 gatilhos emocionais? Se NÃO → reescrever
- Tem pelo menos 1 padrão de lift positivo? Se NÃO → reescrever
"""

# ============================================================
# ANTI-AI SLOP
# ============================================================
_ANTI_AI_SLOP = """
PADRÕES PROIBIDOS NA COPY:
- "Não é X, é Y" / "Não é sobre X, é sobre Y"
- "E isso muda tudo"
- "No fim das contas" / "Ao final do dia"
- "A pergunta fica:" / "A questão é:"
- "De forma X" (vaga)
- "Cada vez mais" (sem dado)
- "Em um mundo onde" / "Vivemos em uma era"
- "É preciso" / "Devemos" / "Você precisa"
- Paralelismos forçados ("X diminui, Y acelera")
- Headlines com "descubra", "saiba", "conheça" como abertura
- "Quando X vira Y", "a ascensão de", "o impacto de"

REGRAS GRAMATICAIS:
- Artigos SEMPRE presentes (um/uma/o/a)
- Conectivos naturais em cada bloco
- Cada bloco soa como parágrafo de reportagem
- Dados com número + fonte + ano
"""

# ============================================================
# COMPLIANCE
# ============================================================
_COMPLIANCE = """
REGRAS DE COMPLIANCE:
━━━ META / INSTAGRAM ━━━
  ❌ NUNCA: "aprovação garantida", "100% aprovado", "sem recusa"
  ❌ NUNCA: urgência falsa ("só hoje", "últimas vagas")
  ❌ NUNCA: antes/depois financeiro
  ✅ PODE: números reais com disclaimer "resultados podem variar"
  ✅ PODE: "processo de análise diferente dos bancos tradicionais"

━━━ HASHTAGS ━━━
  - 3 de nicho + 4 de comportamento + 3 de alcance + 2 de tendência
  - Máximo 12, todas relevantes

━━━ REGRA GERAL ━━━
  Se faz promessa absoluta → suavize
  Se discrimina ou exclui → reescreva
  Se usa urgência artificial → troque por consequência natural
"""

# ============================================================
# SCROLL-STOP VISUAL
# ============================================================
_SCROLL_STOP_VISUALS = """
PSICOLOGIA DO VISUAL SCROLL-STOP:
1. EMOÇÃO VISÍVEL — rostos com emoção forte (choque, alívio, raiva)
2. TENSÃO OU CONTRASTE — conflito visual (claro vs escuro)
3. MOMENTO CAPTURADO — vida real, não pose estática
4. CLOSE-UP OU ÂNGULO INCOMUM
5. IDENTIFICAÇÃO IMEDIATA — cena que o público reconhece
6. PARA VÍDEO: movimento real, não pose

REGRA: se a cena não faria parar o dedo no scroll, reescreva.
"""


# ============================================================
# SYSTEM PROMPT
# ============================================================
_SYSTEM = """\
Você é um dos melhores copywriters e estrategistas de conteúdo do Brasil, \
calibrado pela metodologia BrandsDecoded — a conta que saiu do zero para \
272 mil seguidores em 14 meses, 100% orgânico, 100% carrossel.

Cada headline passa por um filtro de 1.168 posts analisados. \
Você conhece os 56 hooks que ultrapassaram 10k likes e os padrões exatos que viralizam.

Regras absolutas:
- Nunca inventar dados, fontes, estatísticas
- Nunca gerar conteúdo motivacional vazio ou AI slop
- Tom jornalístico — como um repórter da Folha de S.Paulo
- Artigos sempre presentes em todos os substantivos
- Conectivos naturais em cada bloco
- Zero estruturas binárias ("não é X, é Y", "menos X, mais Y", "sem X. sem Y.")
- Zero cacoetes de IA ("e isso muda tudo", "no fim das contas", "ao final do dia")
- Dados sempre com número + fonte + ano
- Headlines IC (1-5): DEVEM ter dois-pontos separando reenquadramento de hook
- Headlines NM (6-10): DEVEM ter EXATAMENTE 3 frases com ponto
- Qualquer headline que não seguir o formato → reescrever antes de entregar
- Headlines reprovadas nunca chegam ao usuário — total entregue sempre = 10 aprovadas

SEMPRE retorne JSON válido — sem texto extra, sem markdown.
"""


# ============================================================
# DATACLASSES
# ============================================================
@dataclass
class HeadlineOption:
    number: int
    headline: str
    triggers: list[str]
    format_type: str    # "IC" or "NM"


@dataclass
class HeadlineResult:
    triagem: str
    eixo: str
    funil: str
    headlines: list[HeadlineOption]


@dataclass
class CopyResult:
    formula: str
    headline_part1: str
    headline_part2: str
    caption: str
    hashtags: list[str]
    image_query: str
    video_query: str
    compliance_flags: list[str] = field(default_factory=list)


# ============================================================
# GENERATE HEADLINES — 10 options
# ============================================================
def generate_headlines(
    topic: str,
    brand: BrandProfile,
    creator_style=None,
    research_data: str = "",
) -> HeadlineResult:
    """
    Generate 10 headlines using Designer AI methodology.
    5 Investigação Cultural + 5 Narrativa Magnética.

    Parameters
    ----------
    research_data : dados da pesquisa Tavily (TopicResearch formatado).
                    Quando fornecido, as headlines DEVEM usar esses dados.
    """
    client = Anthropic()

    brand_context = f"""
MARCA: {brand.client_name}
NICHO: {brand.subniche}
TOM DE VOZ: {brand.tone}
PILARES: {", ".join(brand.content_pillars)}
PÚBLICO: {brand.audience.description} ({brand.audience.age_range})
DORES: {" | ".join(brand.audience.pains)}
LINGUAGEM: {" | ".join(brand.audience.language)}
HANDLE: {brand.handle or "@" + brand.slug}
"""

    creator_block = ""
    if creator_style is not None:
        from designer.research.creator_style import style_to_prompt_block
        creator_block = style_to_prompt_block(creator_style)

    research_block = ""
    if research_data:
        research_block = f"""
━━━ DADOS DA PESQUISA (OBRIGATÓRIO USAR NAS HEADLINES) ━━━
{research_data}

REGRA CRÍTICA: As headlines DEVEM conter dados, números, nomes ou fenômenos da pesquisa acima.
Headlines genéricas que existiriam SEM esses dados são automaticamente reprovadas.
"""

    prompt = f"""
TEMA DO POST: {topic}

PERFIL DA MARCA:
{brand_context}

━━━ FORMATOS DE HEADLINE ━━━
{_HEADLINE_FORMATS}

━━━ PADRÕES DE LIFT E GATILHOS ━━━
{_LIFT_PATTERNS}

━━━ CHECKLIST DE REJEIÇÃO ━━━
{_REJECTION_CHECKLIST}

━━━ ANTI-AI SLOP ━━━
{_ANTI_AI_SLOP}
{creator_block}
{research_block}

━━━ TAREFA ━━━

PASSO 1 — TRIAGEM:
Analise o tema (e os dados da pesquisa, se fornecidos) e extraia:
- Transformação central (o que mudou)
- Fricção (a tensão real)
- Ângulo narrativo dominante
- Classifique: Eixo (Mercado/Cases/Notícias/Cultura/Produto) e Funil (Topo/Meio/Fundo)

PASSO 2 — HEADLINES:
Gere exatamente 10 headlines:
- Headlines 1-5: formato Investigação Cultural (IC) — OBRIGATÓRIO ter dois-pontos
- Headlines 6-10: formato Narrativa Magnética (NM) — OBRIGATÓRIO ter 3 frases com ponto
- Cada headline deve ter pelo menos 2 gatilhos emocionais
- Cada headline deve ter pelo menos 1 padrão de lift positivo
- Distribuição: 1.Reenquadramento 2.Conflito oculto 3.Implicação sistêmica 4.Contradição 5.Ameaça/oportunidade 6.Nomeação 7.Diagnóstico cultural 8.Inversão 9.Ambição de mercado 10.Mecanismo social

PASSO 3 — VALIDAÇÃO:
Rode CADA headline pelo checklist de rejeição. Se falhar, reescreva antes de entregar.

Retorne SOMENTE este JSON:
{{
  "triagem": "1 frase com o ângulo central extraído",
  "eixo": "Mercado|Cases|Notícias|Cultura|Produto",
  "funil": "Topo|Meio|Fundo",
  "headlines": [
    {{
      "number": 1,
      "headline": "headline completa aqui",
      "triggers": ["Curiosidade", "Identidade"],
      "format_type": "IC"
    }},
    ...mais 9 headlines...
  ]
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw.strip())

    headlines = [
        HeadlineOption(
            number=h["number"],
            headline=h["headline"],
            triggers=h.get("triggers", []),
            format_type=h.get("format_type", "IC" if h["number"] <= 5 else "NM"),
        )
        for h in data.get("headlines", [])
    ]

    return HeadlineResult(
        triagem=data.get("triagem", ""),
        eixo=data.get("eixo", "Cultura"),
        funil=data.get("funil", "Topo"),
        headlines=headlines,
    )


# ============================================================
# GENERATE COPY — full post (backward compatible)
# ============================================================
def generate(topic: str, brand: BrandProfile, creator_style=None) -> CopyResult:
    """
    Generate complete copy for a post. Backward compatible with v4.
    Uses enhanced Designer AI methodology internally.
    """
    client = Anthropic()

    brand_context = f"""
MARCA: {brand.client_name}
NICHO: {brand.subniche}
TOM DE VOZ: {brand.tone}
PILARES: {", ".join(brand.content_pillars)}
PÚBLICO: {brand.audience.description} ({brand.audience.age_range})
DORES: {" | ".join(brand.audience.pains)}
LINGUAGEM: {" | ".join(brand.audience.language)}
HANDLE: {brand.handle or "@" + brand.slug}
"""

    creator_block = ""
    if creator_style is not None:
        from designer.research.creator_style import style_to_prompt_block
        creator_block = style_to_prompt_block(creator_style)

    prompt = f"""
TEMA DO POST: {topic}

PERFIL DA MARCA:
{brand_context}

━━━ FORMATOS DE HEADLINE ━━━
{_HEADLINE_FORMATS}

━━━ PADRÕES DE LIFT ━━━
{_LIFT_PATTERNS}

━━━ ANTI-AI SLOP ━━━
{_ANTI_AI_SLOP}

━━━ COMPLIANCE ━━━
{_COMPLIANCE}

━━━ VISUAL SCROLL-STOP ━━━
{_SCROLL_STOP_VISUALS}
{creator_block}

━━━ TAREFA ━━━

Gere o copy completo para este post:

PASSO 1 — HEADLINE:
- Use formato Investigação Cultural: [Reenquadramento]: [Hook]
- Mínimo 2 gatilhos emocionais
- Mínimo 1 padrão de lift positivo
- Parte 1: setup (máx 8 palavras) | Parte 2: virada (máx 8 palavras)

PASSO 2 — LEGENDA:
- Parágrafo 1: dor ou situação (identificação)
- Parágrafo 2: revelação ou dado
- Parágrafo 3: prova ou lógica
- Parágrafo 4: próximo passo natural
- Tom: conversa entre iguais, tom jornalístico
- Sem estruturas binárias, sem cacoetes de IA

PASSO 3 — COMPLIANCE CHECK

PASSO 4 — HASHTAGS (3 nicho + 4 comportamento + 3 alcance + 2 tendência)

PASSO 5 — QUERIES VISUAIS (inglês, 5-9 palavras cada)

Retorne SOMENTE este JSON:
{{
  "formula": "IC|NM",
  "headline_part1": "SETUP EM CAIXA ALTA",
  "headline_part2": "VIRADA EM CAIXA ALTA",
  "caption": "Legenda completa",
  "hashtags": ["#hashtag1", "#hashtag2"],
  "image_query": "scroll-stopping photo scene in english",
  "video_query": "scroll-stopping video scene in english",
  "compliance_flags": ["alerta 1 se houver"]
}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw.strip())

    return CopyResult(
        formula=data["formula"],
        headline_part1=data["headline_part1"].upper(),
        headline_part2=data["headline_part2"].upper(),
        caption=data["caption"],
        hashtags=data.get("hashtags", []),
        image_query=data.get("image_query", f"{brand.niche} {brand.subniche}"),
        video_query=data.get("video_query", data.get("image_query", f"{brand.niche} {brand.subniche}")),
        compliance_flags=data.get("compliance_flags", []),
    )
