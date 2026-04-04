"""
Copy Engine — Prompt Master Senior
Gera copy de alto impacto respeitando os limites das plataformas.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from anthropic import Anthropic
from designer.brand.profile import BrandProfile


# ============================================================
# FÓRMULAS DE HEADLINE
# ============================================================
_FORMULAS = """
F1 — CONTEXTO + PROVOCAÇÃO
  Estrutura: "[Contexto conhecido]: [Afirmação que inverte a expectativa]"
  Exemplo: "NEGATIVADO HÁ 3 ANOS: O QUE OS BANCOS NÃO QUEREM QUE VOCÊ DESCUBRA"
  Quando usar: tema com situação reconhecível + revelação inesperada.

F2 — AFIRMAÇÃO BOLD + PERGUNTA
  Estrutura: "[Verdade que dói ou surpreende]: [Pergunta que o público já se faz em silêncio]"
  Exemplo: "SEU SCORE BAIXO NÃO É O PROBLEMA: ENTÃO POR QUE CONTINUAM TE NEGANDO?"
  Quando usar: mitos, crenças limitantes, contradições do mercado.

F3 — DADO + CONSEQUÊNCIA
  Estrutura: "[Número ou fato concreto]: [O que isso significa para o público]"
  Exemplo: "7 EM CADA 10 BRASILEIROS TÊM O NOME SUJO: E A MAIORIA NEM SABE POR QUÊ"
  Quando usar: estatísticas reais, pesquisas, tendências com impacto direto.

F4 — PROVOCAÇÃO PURA
  Estrutura: "[Nome do problema que o público vive]: [Virada contraintuitiva]"
  Exemplo: "A RECUSA DO BANCO: O SINAL DE QUE VOCÊ ESTAVA BATENDO NA PORTA ERRADA"
  Quando usar: reframing de situação negativa em oportunidade.

REGRA DE SPLIT:
  - Parte 1: setup, contexto, nome do problema — termina com ":" — TOM SÉRIO
  - Parte 2: a virada, o dado chocante, a revelação — TOM PROVOCADOR
  - Ambas em CAIXA ALTA, máximo 8 palavras cada
"""


# ============================================================
# GATILHOS PSICOLÓGICOS — MASTER LIST
# ============================================================
_TRIGGERS = """
GATILHOS PERMITIDOS E COMO USAR (jogue nas 4 linhas, no limite):

1. CURIOSIDADE COM GAP DE INFORMAÇÃO
   Crie uma lacuna entre o que o público sabe e o que você vai revelar.
   ✅ "o que os bancos não te contam sobre score"
   ✅ "a cláusula que ninguém lê no contrato do cartão"
   ❌ "segredo proibido que eles escondem" (sensacionalismo que derruba alcance)

2. PROVA SOCIAL IMPLÍCITA
   Mostre que outros já fizeram — sem inventar números.
   ✅ "milhares de brasileiros com nome sujo já conseguiram"
   ✅ "quem estava na mesma situação há 6 meses hoje tem limite de R$2.000"
   ❌ "100% aprovado" / "garantido" (proibido em anúncios financeiros)

3. IDENTIDADE E PERTENCIMENTO
   Fale para um grupo específico que se reconhece.
   ✅ "para quem foi recusado em todo banco e ainda não desistiu"
   ✅ "se você está reconstruindo sua vida financeira, este post é para você"
   ❌ "para negativados" como targetização explícita em anúncio pago (Special Ad Category)

4. MEDO DE PERDA (LOSS AVERSION)
   O que ele perde se não agir — sem urgência falsa.
   ✅ "cada mês sem crédito é um mês a mais longe da sua reconstrução"
   ✅ "enquanto você espera o score subir, o custo de vida não espera"
   ❌ "só até hoje" / "últimas vagas" (urgência artificial = shadowban)

5. REFRAMING DE IDENTIDADE
   Transforme a dor em identidade positiva.
   ✅ "negativado não é fracassado — é alguém que o sistema ainda não entendeu"
   ✅ "nome sujo não é destino, é um estado temporário"
   ❌ atacar bancos pelo nome (risco de processo + flagging)

6. AUTORIDADE SEM ARROGÂNCIA
   Demonstre conhecimento, não superioridade.
   ✅ "depois de analisar 3.000 casos de recusa de crédito, percebemos que..."
   ✅ "o que aprendemos trabalhando com quem foi recusado em todo banco:"
   ❌ "somos os melhores do mercado" (afirmação não verificável = banida)

7. ESPECIFICIDADE QUE GERA CREDIBILIDADE
   Números específicos convencem mais que generalizações.
   ✅ "aprovação em 48 horas" (se for verdade)
   ✅ "sem consulta ao SPC em 92% dos casos" (se for real e verificável)
   ❌ "aprovação instantânea garantida" (promessa absoluta = proibida)

8. CONTRADIÇÃO E QUEBRA DE PADRÃO
   Contrarie o óbvio para forçar o stop no scroll.
   ✅ "ter nome sujo pode ser a coisa mais honesta que aconteceu com você"
   ✅ "o banco te recusou. Isso é um dado, não uma sentença."
"""


# ============================================================
# COMPLIANCE POR PLATAFORMA E NICHO
# ============================================================
_COMPLIANCE = """
REGRAS DE COMPLIANCE — JOGUE NO LIMITE, NÃO CRUZE A LINHA:

━━━ META / INSTAGRAM / FACEBOOK ━━━

FINANCEIRO (crédito, empréstimo, cartão) — CATEGORIA ESPECIAL:
  ❌ NUNCA use: "aprovação garantida", "100% aprovado", "sem recusa"
  ❌ NUNCA use: discriminação por raça, gênero, localização em copy de anúncio
  ❌ NUNCA use: "score não importa" (Meta interpreta como enganoso)
  ❌ NUNCA use: urgência falsa — "só hoje", "últimas vagas", "expira em X horas"
  ❌ NUNCA use: antes/depois financeiro ("estava endividado, agora tenho R$50k")
  ✅ PODE usar: "processo de análise diferente dos bancos tradicionais"
  ✅ PODE usar: "muitos clientes com histórico restrito conseguiram aprovação"
  ✅ PODE usar: "análise humanizada, não só pelo score"
  ✅ PODE usar: números reais e verificáveis com disclaimer "resultados podem variar"

SAÚDE / FITNESS:
  ❌ NUNCA use: "perca X kg em Y dias", "resultado garantido"
  ❌ NUNCA use: imagens de before/after com claims de tempo específico
  ✅ PODE usar: "muitos clientes relatam resultados em semanas"
  ✅ PODE usar: depoimentos reais com nome e consentimento

BELEZA / ESTÉTICA:
  ❌ NUNCA use: claims médicos sem laudo ("elimina gordura", "cura")
  ✅ PODE usar: "aparência mais firme", "pele com mais viço"

━━━ ALGORITMO / SHADOWBAN ━━━

Palavras que derrubam alcance orgânico (evite mesmo em post orgânico):
  ❌ "siga", "curta", "compartilhe" em excesso — reduz alcance
  ❌ Emojis em excesso (mais de 5 por parágrafo)
  ❌ Links externos na legenda (Instagram penaliza)
  ❌ Hashtags genéricas demais (#amor, #vida) junto com muitas de nicho
  ✅ Máximo 10-15 hashtags, todas relevantes ao nicho
  ✅ CTA natural: "salva esse post", "me conta nos comentários"
  ✅ Hashtags no primeiro comentário > na legenda (debate em aberto, use com moderação)

━━━ TIKTOK ━━━
  ❌ Claims de resultado financeiro específico
  ❌ Conteúdo que pareça anúncio não declarado (obrigado #publi ou #ad)
  ✅ Narrativa UGC — mais tolerância para gatilhos emocionais
  ✅ Tendências de áudio aumentam alcance mais que qualquer copy

━━━ REGRA GERAL ━━━
  Antes de finalizar qualquer copy, pergunte:
  1. Esse texto faz promessa absoluta que não pode ser garantida? → Suavize
  2. Esse texto discrimina ou exclui grupos protegidos? → Reescreva
  3. Esse texto usa urgência artificial? → Troque por escassez real ou consequência natural
  4. Esse texto pode ser interpretado como enganoso por alguém mal-intencionado? → Ajuste
  Se todas as respostas forem NÃO → pode publicar.
"""


# ============================================================
# SCROLL-STOP VISUAL
# ============================================================
_SCROLL_STOP_VISUALS = """
PSICOLOGIA DO VISUAL QUE PARA O SCROLL:

1. EMOÇÃO VISÍVEL — rostos com emoção forte (choque, alívio, raiva, esperança)
   ❌ "person holding credit card"
   ✅ "shocked young man staring at phone screen with credit card, dim dramatic light"

2. TENSÃO OU CONTRASTE — conflito visual (claro vs escuro, riqueza vs pobreza)
   ❌ "woman at the gym"
   ✅ "exhausted woman sitting on gym floor head down, single spotlight"

3. MOMENTO CAPTURADO — não pose estática, parece vida real
   ❌ "businessman smiling at camera"
   ✅ "man running out of bank looking desperate, motion blur background"

4. CLOSE-UP OU ÂNGULO INCOMUM
   ❌ "pile of money"
   ✅ "extreme close-up of crumpled bills on dark floor, one coin shining"

5. IDENTIFICAÇÃO IMEDIATA — cena que o público reconhece como a própria vida
   ❌ "family at dinner"
   ✅ "couple arguing over bills on kitchen table at night, stressed expressions"

6. PARA VÍDEO: movimento real, não pose
   ❌ "city skyline"
   ✅ "timelapse busy city street night neon lights reflecting wet pavement"

REGRA: se a cena não faria parar o dedo no scroll, reescreva.
"""


# ============================================================
# SYSTEM PROMPT MASTER
# ============================================================
_SYSTEM = """\
Você é um dos melhores copywriters e estrategistas de conteúdo do Brasil.

Sua especialidade é criar conteúdo que converte — carrosseis e Reels que param o scroll,
geram identificação imediata e levam à ação — respeitando os limites das plataformas.

Você conhece as políticas do Meta, Instagram, TikTok e Google melhor do que a maioria dos
profissionais de marketing. Você sabe exatamente onde está a linha e joga rente a ela,
sem nunca cruzar — porque copywriter banido não fatura.

Você entende que gatilho emocional não é manipulação — é falar a verdade de um jeito que
ressoa. O segredo é a especificidade: quanto mais específico e verdadeiro, mais poderoso
e mais seguro para as plataformas.

Suas regras pessoais:
- Nunca prometa o que não pode ser garantido
- Nunca invente números — use os reais ou use linguagem qualitativa
- Nunca use urgência artificial — use consequência natural
- Sempre escreva como se um advogado e um cliente fossem ler juntos
- O copy mais seguro é o copy mais verdadeiro

SEMPRE retorne JSON válido — sem texto extra, sem markdown.
"""


# ============================================================
# DATACLASS
# ============================================================
@dataclass
class CopyResult:
    formula: str
    headline_part1: str
    headline_part2: str
    caption: str
    hashtags: list[str]
    image_query: str
    video_query: str
    compliance_flags: list[str] = field(default_factory=list)  # alertas de compliance


# ============================================================
# GENERATE
# ============================================================
def generate(topic: str, brand: BrandProfile, creator_style=None) -> CopyResult:
    """
    Parameters
    ----------
    creator_style : CreatorStyle | None
        Estilo extraído de um criador de referência (via creator_style.py).
        Quando fornecido, injeta o bloco de estilo no prompt para a legenda
        soar com a voz do criador adaptada ao nicho.
    """
    client = Anthropic()

    brand_context = f"""
MARCA: {brand.client_name}
NICHO: {brand.subniche}
TOM DE VOZ: {brand.tone}
PILARES: {", ".join(brand.content_pillars)}
PÚBLICO: {brand.audience.description} ({brand.audience.age_range})
DORES DO PÚBLICO: {" | ".join(brand.audience.pains)}
LINGUAGEM DO PÚBLICO: {" | ".join(brand.audience.language)}
HANDLE: {brand.handle or "@" + brand.slug}
"""

    # Bloco de estilo do criador (opcional)
    creator_block = ""
    if creator_style is not None:
        from designer.research.creator_style import style_to_prompt_block
        creator_block = style_to_prompt_block(creator_style)

    prompt = f"""
TEMA DO POST: {topic}

PERFIL DA MARCA:
{brand_context}

━━━ FÓRMULAS DE HEADLINE ━━━
{_FORMULAS}

━━━ GATILHOS PSICOLÓGICOS PERMITIDOS ━━━
{_TRIGGERS}

━━━ COMPLIANCE — REGRAS DE PLATAFORMA ━━━
{_COMPLIANCE}

━━━ VISUAL SCROLL-STOP ━━━
{_SCROLL_STOP_VISUALS}
{creator_block}

━━━ TAREFA ━━━

Gere o copy completo para este post. Siga esta ordem mental:

PASSO 1 — HEADLINE:
- Escolha a fórmula mais adequada ao tema e às dores do público
- Use pelo menos 2 gatilhos da lista — no limite, sem cruzar
- Seja específico ao nicho — generalidade não converte
- Parte 1: setup (máx 6 palavras) | Parte 2: virada (máx 7 palavras)

PASSO 2 — LEGENDA:
- Parágrafo 1: dor ou situação que o público vive (identificação)
- Parágrafo 2: revelação ou dado que muda a perspectiva
- Parágrafo 3: prova ou lógica que sustenta
- Parágrafo 4: próximo passo natural (não grite, guie)
- Tom: conversa entre iguais — não palestra, não anúncio
- Frases curtas. Respiração entre parágrafos. Máx 3 linhas por parágrafo.

PASSO 3 — COMPLIANCE CHECK:
- Releia tudo e identifique qualquer frase problemática
- Se encontrar, reescreva ANTES de retornar
- Liste em compliance_flags qualquer ponto que merece atenção do cliente

PASSO 4 — HASHTAGS:
- 3 de nicho específico + 4 de comportamento + 3 de alcance + 2 de tendência
- Todas relevantes — sem encher de genérico

PASSO 5 — QUERIES VISUAIS:
- image_query: foto scroll-stop em inglês (5-9 palavras)
- video_query: cena com movimento em inglês (5-9 palavras)

Retorne SOMENTE este JSON:
{{
  "formula": "F1|F2|F3|F4",
  "headline_part1": "SETUP EM CAIXA ALTA",
  "headline_part2": "VIRADA EM CAIXA ALTA",
  "caption": "Legenda completa pronta para publicar",
  "hashtags": ["#hashtag1", "#hashtag2"],
  "image_query": "scroll-stopping photo scene in english",
  "video_query": "scroll-stopping video scene with movement in english",
  "compliance_flags": ["alerta 1 se houver", "alerta 2 se houver"]
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
