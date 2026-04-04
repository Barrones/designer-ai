# DESIGNER AI — BRIEFING COMPLETO PARA CLAUDE CODE

## O QUE É ESTE PROJETO
Uma ferramenta de IA que gera conteúdo visual automatizado para Instagram (carrosséis, posts, stories) e anúncios digitais (Google Display HTML5, Meta Ads). O sistema pesquisa tendências em tempo real, gera copy e cria os visuais prontos para publicar — tudo automatizado, rodando 24/7.

## INSPIRAÇÃO / CONCORRENTE (BrandsDecoded)
A BrandsDecoded (@brandsdecoded_) é um perfil no Instagram com 250K+ seguidores que posta a cada 30 minutos, todos os dias. Eles vendem um infoproduto manual (templates + prompts ChatGPT) por R$297. O que queremos é criar a FERRAMENTA que faz isso automaticamente — não templates manuais, mas geração real de imagens prontas.

## VISÃO DO PRODUTO
- **Fase 1:** Ferramenta para uso pessoal (CLI + API local)
- **Fase 2:** SaaS onde o cliente informa o nicho e o sistema gera tudo automaticamente

---

## PADRÕES VISUAIS ANALISADOS (da BrandsDecoded)

### Layout da Capa de Carrossel (formato 1080x1350 — Instagram)
```
┌──────────────────────────────────────────────┐
│ HEADER BAR (gradiente azul→vermelho, 40px)   │
│ "Powered by [Nome]"  "@handle"  "2026 //"    │
├──────────────────────────────────────────────┤
│                                              │
│         ┌──────────────────────┐             │
│         │                      │             │
│         │   FOTO / IMAGEM      │             │
│         │   DE CONTEXTO        │  ← 60% sup  │
│         │   (pessoa, produto,  │             │
│         │    cenário real)      │             │
│         │                      │             │
│         └──────────────────────┘             │
│                                              │
│    ☀️ @handle ✓                               │
│                                              │
│    HEADLINE EM CAIXA ALTA                    │
│    COM PALAVRAS-CHAVE EM                     │
│    COR DE DESTAQUE + ITÁLICO.                │
│                                              │
├──────────────────────────────────────────────┤
│ FOOTER BAR (gradiente matching header, 40px) │
└──────────────────────────────────────────────┘
```

### Tipografia
- **Headline:** Font condensed/compressed sans-serif (Anton, Oswald Black, Bebas Neue). SEMPRE uppercase. Palavras de destaque em itálico + cor.
- **Header/Footer UI:** Sans-serif geométrica (Inter, Montserrat). Light weight, tracking largo, lowercase.
- **Handle:** Sans-serif geométrica, medium weight.

### Paleta de Cores
- **Fundo:** Foto real com overlay gradiente escuro (preto, 40-60% opacidade, de baixo para cima)
- **Texto principal:** Branco puro (#FFFFFF)
- **Destaque 1:** Vermelho/coral (#E63946 ou #FF3B3B) — usado em itálico
- **Destaque 2:** Laranja (#FF6B35)
- **Destaque 3:** Amarelo (#FFD600)
- **Header/Footer bars:** Gradiente linear (azul escuro #1A1A8B → vermelho #8B0000)

### Fórmulas de Headline (4 padrões identificados)

**F1 — Contexto + Provocação:**
"O DOM DE ESTRAGAR TUDO: **COMO NEYMAR TRANSFORMOU A NARRATIVA EM POLÊMICA EM MENOS DE DOIS MINUTOS.**"

**F2 — Afirmação Bold + Pergunta:**
"O PERSONAL TRAINER DO FUTURO: **POR QUE O PROFISSIONAL QUE ENTENDE DE CONTEÚDO VAI DOMINAR O MERCADO FITNESS?**"

**F3 — Notícia + Dado Impactante:**
"Heinz lança Ketchup Zero e aposta **R$ 50 milhões** para liderar o mercado no Brasil"

**F4 — Provocação Pura:**
"A ARMADILHA DO PERFECCIONISMO: **POR QUE O POST IMPERFEITO VALE MAIS DO QUE O PERFEITO QUE NUNCA SAIU.**"

**Regra de split:** Primeira parte em branco → segunda parte (a mais provocativa) em COR DE DESTAQUE + ITÁLICO.

### Elementos Fixos
- Barra header e footer com gradiente (sempre presentes)
- "Powered by [Nome do Sistema]" — canto superior esquerdo
- "@handle" — centro superior
- "Ano //" — canto superior direito
- Logo/ícone + @handle + ✓ verificado — sobre a imagem, acima da headline

---

## ARQUITETURA TÉCNICA

### Stack
- **Python 3.12+**
- **Framework de agentes:** Agno (já em uso no projeto irmão)
- **LLM:** Claude (Anthropic) — motor de decisão, copy, headlines
- **Pesquisa:** Tavily (busca web), pytrends (Google Trends)
- **Imagens:** Pillow/cairosvg para rasterizar SVG→PNG, ou html2image
- **Vídeo:** TopView API (avatar com dublagem) — já funcional
- **Storage:** SQLite para histórico, Google Drive para arquivos
- **Scheduling:** APScheduler ou similar para rodar a cada 30 min
- **Fontes:** Google Fonts (Anton, Oswald, Bebas Neue, Inter, Montserrat)

### Estrutura de Pastas Planejada
```
Designer/
├── pyproject.toml
├── .env
├── designer/
│   ├── __init__.py
│   ├── agent.py              # Agente principal (Claude + Agno)
│   ├── config.py             # Configurações, cores, fontes
│   ├── scheduler.py          # Agendamento de posts (30 em 30 min)
│   │
│   ├── research/             # Módulo de pesquisa de tendências
│   │   ├── __init__.py
│   │   ├── trends.py         # Google Trends, categorias em alta
│   │   ├── viral.py          # Produtos/assuntos virais (Tavily, TikTok)
│   │   └── news.py           # Notícias do momento por nicho
│   │
│   ├── copy/                 # Módulo de geração de copy
│   │   ├── __init__.py
│   │   ├── headlines.py      # Gerador de headlines (4 fórmulas)
│   │   ├── hooks.py          # Hooks para Reels/Shorts
│   │   ├── captions.py       # Legendas para Instagram
│   │   └── scripts.py        # Roteiros completos (Reels, Shorts)
│   │
│   ├── visual/               # Módulo de geração visual
│   │   ├── __init__.py
│   │   ├── carousel.py       # Gerador de carrosséis (SVG→PNG)
│   │   ├── templates/        # Templates SVG base
│   │   │   ├── cover.svg     # Template da capa
│   │   │   ├── content.svg   # Template slide de conteúdo
│   │   │   └── cta.svg       # Template slide final (CTA)
│   │   ├── html5_ads.py      # Gerador HTML5 Google Display
│   │   ├── renderer.py       # SVG→PNG, HTML→imagem
│   │   └── fonts/            # Fontes locais
│   │
│   ├── publishing/           # Módulo de publicação
│   │   ├── __init__.py
│   │   ├── instagram.py      # Publicação via API do Instagram
│   │   └── drive.py          # Upload Google Drive
│   │
│   └── prompts/              # System prompts
│       ├── researcher.md     # Prompt do pesquisador de tendências
│       ├── copywriter.md     # Prompt do copywriter
│       └── designer.md       # Prompt do designer visual
│
├── output/                   # Posts gerados
│   ├── carousels/
│   ├── html5_ads/
│   └── scripts/
│
└── tests/
```

### Fluxo Principal (Pipeline Automatizado)
```
A cada 30 minutos:

1. PESQUISA
   ├── Buscar tendências do momento (Google Trends)
   ├── Buscar notícias virais do nicho (Tavily)
   ├── Identificar assuntos com potencial de engajamento
   └── Retornar: tema + dados + fontes

2. COPY (Claude)
   ├── Receber tema + dados da pesquisa
   ├── Gerar headline (usando as 4 fórmulas)
   ├── Definir split de cor (parte branca vs. parte destaque)
   ├── Gerar legenda completa estilo editorial
   ├── Gerar hashtags relevantes
   └── Retornar: headline, legenda, hashtags, sugestão de imagem

3. VISUAL
   ├── Buscar imagem de contexto (Unsplash API ou similar)
   ├── Aplicar no template SVG (inserir imagem, headline, cores)
   ├── Renderizar SVG → PNG (1080x1350)
   └── Retornar: imagem pronta

4. PUBLICAÇÃO
   ├── Salvar em output/carousels/
   ├── Upload Google Drive
   ├── (futuro) Publicar direto no Instagram via API
   └── Logar no SQLite
```

---

## O QUE CONSTRUIR PRIMEIRO (PRIORIDADE)

### Fase 1 — Template SVG + Renderer (COMEÇAR AQUI)
1. Criar template SVG da capa do carrossel (1080x1350) com os placeholders
2. Criar função Python que recebe (headline, imagem_url, cor_destaque, handle) e gera o PNG final
3. Usar Pillow ou cairosvg para renderizar
4. Testar com dados hardcoded

### Fase 2 — Motor de Copy
1. Criar as 4 fórmulas de headline como funções
2. Integrar Claude para gerar headlines a partir de um tema
3. Auto-split: Claude decide qual parte fica branca e qual fica colorida/itálica

### Fase 3 — Pesquisa de Tendências
1. Migrar market_research.py do projeto existente
2. Adicionar busca de notícias por nicho
3. Ranking de potencial viral

### Fase 4 — Pipeline Completo
1. Conectar Pesquisa → Copy → Visual
2. Agendar com APScheduler (30 em 30 min)
3. Gerar e salvar automaticamente

### Fase 5 — Formatos Extras
1. HTML5 Google Display Ads (300x250, 728x90, 160x600)
2. Roteiros de Reels/Shorts
3. Stories templates

---

## PROJETO EXISTENTE (REFERÊNCIA)
O projeto "Agente de IA para criação de conteúdo" no diretório irmão já tem:
- Agente Claude com framework Agno (agent.py)
- Bot Discord integrado (bot.py)
- Pesquisa de mercado completa (market_research.py) — Google Trends, Tavily, TikTok, AliExpress
- Transcrição de vídeos (transcripter.py)
- Geração de vídeo com avatar (TopView API no bot.py)
- Prompts detalhados de copywriting (prompts/copywriter.md)
- Google Drive/Sheets integrados

Reutilize o que for possível (especialmente market_research.py e as integrações).

---

## VARIÁVEIS DE AMBIENTE NECESSÁRIAS
```
ANTHROPIC_API_KEY=       # Claude API
TAVILY_API_KEY=          # Busca web
GROQ_API_KEY=            # Whisper (transcrição)
TOPVIEW_API_KEY=         # Geração de vídeo
TOPVIEW_UID=             # TopView user ID
GOOGLE_CREDENTIALS_FILE= # Service account JSON
GOOGLE_DRIVE_FOLDER_ID=  # Pasta no Drive
UNSPLASH_ACCESS_KEY=     # Busca de imagens (novo)
```

---

## REGRAS DE QUALIDADE
- Headlines SEMPRE em caixa alta
- Palavras de destaque em cor + itálico (não sublinhado, não negrito)
- Overlay na foto SEMPRE presente (gradiente preto, 40-60%)
- Texto deve ser legível sobre qualquer foto
- Formato 1080x1350 (Instagram feed/carrossel)
- Fontes: Anton para headlines, Inter para UI elements
