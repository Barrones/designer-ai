# Designer AI — Princípios de Design Visual (Knowledge File)

> Regras visuais que garantem legibilidade, hierarquia e impacto em todo carrossel.

---

## 1. Hierarquia Visual em 3 Níveis

Todo slide deve ter exatamente 3 níveis de informação:

### Nível 1 — Âncora (Anchor)

O elemento que o olho encontra primeiro. Ocupa o maior peso visual.

| Slide | Âncora |
|-------|--------|
| Capa | Headline (52-64px, ExtraBold) |
| Dark/Light | Título interno (32-40px, Bold) |
| CTA | Keyword box |
| Com big stat | O número (72-96px, Black) |

**Regra:** Apenas UM elemento âncora por slide. Se houver big stat E headline, o big stat é a âncora e a headline reduz para 28px.

### Nível 2 — Contexto (Context)

Texto que expande a âncora. Peso visual médio.

- Corpo do texto (22-26px, Regular)
- Card headline (24-28px, SemiBold)
- Subtítulo da capa (22px, Regular)

**Regra:** O contexto nunca compete visualmente com a âncora. Sempre em peso Regular ou SemiBold, nunca Bold.

### Nível 3 — Metadado (Metadata)

Informação periférica que reforça credibilidade sem competir por atenção.

- Tags (14px, uppercase)
- Brand bar (13px, uppercase, 50% opacity)
- Progress bar
- Caption de imagem (14px)
- Fonte/crédito (12px)

**Regra:** Metadados são quase invisíveis. Opacidade ≤ 60%, tamanho ≤ 16px.

---

## 2. Ritmo Dark/Light

A alternância entre slides escuros e claros cria ritmo visual e evita fadiga.

### Regras do ritmo

1. **A capa é sempre única** — não conta como dark nem light.
2. **O primeiro slide de conteúdo (slide 2) é SEMPRE dark** — contraste imediato com a capa.
3. **O último slide de conteúdo (antes do CTA) é SEMPRE dark** — transição suave para o CTA gradient.
4. **O CTA é sempre gradient** — usar variável `--G`.
5. **No miolo, alternar estritamente** — dark, light, dark, light...
6. **Nunca dois slides da mesma temperatura seguidos** (exceto capa→dark e dark→CTA).

### Por que funciona

- Dark slides: intensidade, destaque para dados, ghost numbers, senso de profundidade.
- Light slides: respiro visual, acessibilidade, legibilidade prolongada, cards e tabelas.
- A alternância mantém o swipe momentum — cada slide parece "novo".

---

## 3. Regra do Terço Inferior

O conteúdo textual deve viver predominantemente no **terço inferior** do slide.

### Implementação

```
┌─────────────────────────┐
│  Accent bar              │
│  Progress bar            │
│                          │
│                          │  ← Terço superior: vazio ou ghost number
│                          │
│                          │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│  ← Linha dos 45%
│                          │
│  [Tag/Label]             │  ← Terço médio: tag + início do conteúdo
│  Título interno          │
│  Corpo do texto          │  ← Terço inferior: conteúdo principal
│  [Card / Componente]     │
│                          │
│  Brand bar               │
└─────────────────────────┘
```

### Exceções

- **Capa com imagem full-bleed**: texto no terço inferior via gradient overlay.
- **Slide com big stat**: o número pode subir para o terço médio, com label abaixo.
- **Slide com tabela longa**: a tabela pode ocupar 60% do slide.

### CSS que implementa isso

O `slide-content` usa `justify-content: flex-end`, empurrando todo o conteúdo para baixo naturalmente.

---

## 4. Escala Tipográfica Completa

| Token | Tamanho | Peso | Line-height | Uso |
|-------|---------|------|-------------|-----|
| `--type-display` | 52-64px | 800 (ExtraBold) | 1.05-1.10 | Cover headline |
| `--type-h1` | 36-40px | 700 (Bold) | 1.15-1.20 | Título interno principal |
| `--type-h2` | 28-32px | 700 (Bold) | 1.20 | Título interno secundário |
| `--type-h3` | 24-28px | 600 (SemiBold) | 1.25 | Card headline |
| `--type-body` | 22-26px | 400 (Regular) | 1.50-1.55 | Corpo de texto |
| `--type-body-sm` | 18-22px | 400 (Regular) | 1.45 | Card body, texto secundário |
| `--type-caption` | 14-16px | 500 (Medium) | 1.35 | Tags, labels |
| `--type-meta` | 12-13px | 500 (Medium) | 1.30 | Brand bar, créditos |
| `--type-stat` | 72-96px | 900 (Black) | 1.00 | Big stat number |

### Regras tipográficas

1. **Máximo 2 famílias tipográficas** por carrossel (headline + body).
2. **Máximo 3 pesos** visíveis por slide (ex: Bold, Regular, Medium).
3. **Nunca use itálico** — é ilegível em telas móveis pequenas.
4. **Letter-spacing** — aumentar 0.03-0.08em em textos uppercase.
5. **Quebra de linha da headline** — forçar `<br>` para evitar viúvas e garantir impacto.

---

## 5. Quando Usar Cada Componente

### Card (`.card-dark` / `.card-light`)

**Usar quando:**
- Precisa destacar uma citação, dado ou definição.
- Quer criar separação visual entre o corpo e um destaque.
- Tem um "box" de informação complementar.

**Não usar quando:**
- O slide já tem outro componente (table, big stat).
- O texto é curto demais para justificar um card (< 15 palavras).

### Table (`.slide-table`)

**Usar quando:**
- Tem dados comparativos (antes/depois, opção A vs B).
- Precisa mostrar 3+ itens estruturados.
- O formato lista não seria claro o suficiente.

**Não usar quando:**
- Tem mais de 5 linhas (cortar ou dividir em 2 slides).
- Os dados não têm relação colunar.

### Big Stat (`.big-stat`)

**Usar quando:**
- Tem UM número impactante que sustenta o argumento.
- O número é surpreendente e merece ser a âncora do slide.
- Exemplos: "73%", "R$ 4.2 bi", "12x mais", "1 em 3".

**Não usar quando:**
- O número não é surpreendente.
- Tem vários números (use table em vez disso).

### Image Box (`.img-box`)

**Usar quando:**
- Precisa mostrar produto, pessoa, lugar dentro de um slide.
- A imagem complementa mas não é a âncora.
- Print de tela, gráfico ou foto ilustrativa.

**Não usar quando:**
- A imagem merece ser full-bleed (use slide dark-img).
- A imagem é decorativa sem valor informacional.

### Arrow Rows (`.arrow-row`)

**Usar quando:**
- Lista de 2-4 itens curtos em sequência.
- Passos de um processo.
- Comparação ponto a ponto.

**Não usar quando:**
- Tem mais de 4 itens (use table ou divida em slides).
- Os itens precisam de explicação longa.

---

## 6. Geração de Paleta a partir de Cor Primária

Recebendo apenas a cor primária (--P), gerar todas as variações:

### Algoritmo

```
INPUT: --P (ex: #1A3A6B)

--PL  = desaturar 60% + clarear para L=95% (HSL)      → fundo light suave
--PD  = escurecer para L=15% mantendo hue              → fundo dark profundo
--LB  = #F5F5F5                                         → fixo (cinza quase branco)
--LR  = #F0F0F0                                         → fixo (cinza relevo)
--DB  = #111111                                         → fixo (preto profundo)
--G   = linear-gradient(135deg, --P, --PD)              → gradiente diagonal
```

### Regras de cor

1. **Cor primária aparece em:** accent bar, progress dots ativos, tags, badges, big stats, card borders, CTA keyword box.
2. **Cor primária NÃO aparece em:** texto de corpo, fundos inteiros (exceto accent bar).
3. **Branco puro (#FFFFFF)** — apenas dentro de cards em slides light.
4. **Preto puro (#000000)** — NUNCA. Usar #111111 (--DB) para dark.
5. **Texto em dark slides** — #FFFFFF com opacidade 85% para corpo, 100% para headlines.
6. **Texto em light slides** — --PD para headlines, rgba(0,0,0,0.75) para corpo.

---

## 7. Princípios de Imagem

### Imagem de Capa

- **Composição:** Sujeito no centro ou terço direito, com espaço para texto no terço inferior esquerdo.
- **Tom:** Consistente com o mood do conteúdo (sério = tons frios, provocativo = alto contraste).
- **Gradient overlay:** OBRIGATÓRIO. De transparente no topo para 95% opacidade na base.
- **Resolução mínima:** 1080px de largura.
- **Formato:** Paisagem ou quadrada (será cortada para 4:5).

### Imagem Interna (Dark-img)

- **Overlay:** MÍNIMO 70% opacidade de preto. Idealmente 75%.
- **Uso:** Máximo 2 slides com imagem interna por carrossel (exceto capa).
- **Função:** Atmosférica, não informacional. O texto deve ser legível sem a imagem.
- **Teste:** Cubra a imagem — o slide ainda funciona? Se sim, a imagem está no papel certo.

### Image Box

- **Tamanho:** Máximo 280px de altura dentro do slide.
- **Border radius:** 16px (--radius).
- **Caption:** Opcional, 14px, sobre gradient na base da imagem.
- **Posição:** Sempre acima ou abaixo do corpo de texto, nunca ao lado (layout vertical mobile-first).

---

## 8. Checklist Visual (10 itens)

Antes de entregar o HTML, verificar TODOS:

| # | Item | Critério |
|---|------|----------|
| 1 | Accent bar presente | Em todos os slides |
| 2 | Brand bar presente | Em todos os slides, texto "Powered by Designer AI" |
| 3 | Progress bar presente | Em todos os slides, dot ativo correto |
| 4 | Alternância dark/light | Sequência correta sem repetição |
| 5 | Hierarquia 3 níveis | Cada slide tem âncora, contexto, metadado |
| 6 | Terço inferior | Conteúdo textual no terço inferior |
| 7 | Contraste WCAG AA | Ratio ≥ 4.5:1 em todo texto |
| 8 | Máximo 60 palavras | Nenhum slide de conteúdo excede |
| 9 | Fontes carregadas | Google Fonts link ou base64 embutido |
| 10 | 1080×1350px | Todos os slides no tamanho correto |

---

## 9. Anti-padrões Visuais (O que NÃO fazer)

| Anti-padrão | Por quê | Alternativa |
|-------------|---------|-------------|
| Texto centralizado verticalmente | Parece apresentação corporativa genérica | Usar flex-end (terço inferior) |
| Mais de 3 cores no slide | Poluição visual | Usar apenas --P, --PD, branco/preto |
| Fontes decorativas/script | Ilegíveis em mobile | Usar apenas sans-serif ou serif editorial |
| Ícones genéricos (💡🚀🎯) | Sinalizam "conteúdo de IA" | Usar arrow rows ou cards |
| Texto sobre imagem sem overlay | Ilegível | Overlay mínimo 70% |
| Sombras exageradas | Parecem anos 2010 | Sombras sutis (var(--shadow-card)) |
| Bordas visíveis em tudo | Poluição | Bordas apenas em cards e tabelas |
| Gradientes multicoloridos | Amador | Gradiente monocromático (--P → --PD) |
| Emojis como elemento de design | Infantiliza | Texto tipográfico puro |
| Slides sem padding | Sufocante | Mínimo 64px lateral |
| Texto menor que 20px no corpo | Ilegível em stories | Mínimo 20px |
| Mais de 2 componentes por slide | Overload | Máximo 1 componente + texto |
