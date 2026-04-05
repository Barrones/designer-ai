# Design System — Princípios Visuais para Carrosséis Instagram

Consultar ANTES de renderizar qualquer carrossel HTML. Define os princípios visuais que fazem um carrossel parecer profissional e não genérico.

**REGRA CRÍTICA DE FONTES:** Nunca usar `<link>` do Google Fonts. Sempre embutir as fontes como base64 via `@font-face` no `<style>` do HTML. Isso garante que o export PNG renderize idêntico ao preview no browser.

---

## 1. Hierarquia Visual — Regra dos 3 Níveis

Todo slide tem exatamente 3 níveis de leitura. Nunca mais, nunca menos.

| Nível | O que é | Peso visual | Exemplo |
|-------|---------|-------------|---------|
| **1 — Âncora** | O elemento que o olho vê primeiro | Maior: headline condensada, número grande, imagem | Headline em 80px |
| **2 — Contexto** | O que explica a âncora | Médio: body text, 38px | Parágrafo explicativo |
| **3 — Metadata** | O que organiza sem competir | Menor: tag, brand bar, progress | Tag em 13px |

**Regra:** Se um slide tem 2 elementos com o mesmo peso visual, um deles precisa mudar.

**Aplicação prática:**
- Slides com headline: headline = nível 1, body = nível 2, tag = nível 3
- Slides sem headline: body com `<strong>` no início = nível 1, resto = nível 2, tag = nível 3
- Slides com tabela: header = nível 1, dados = nível 2, fonte = nível 3
- Slides com número grande: número = nível 1, label = nível 2, tag = nível 3

---

## 2. Ritmo Visual — Alternância Dark/Light

- **Dark slides** = tensão, revelação, mecanismo. Tom mais sério.
- **Light slides** = dados, prova, aplicação prática. Tom mais acessível.
- **Gradient slide** = direção, chamada à ação implícita. Tom de urgência.

**Regra de quebra:** nunca 3 slides consecutivos do mesmo tipo (dark-dark-dark ou light-light-light).

**Regra de densidade:**
- Dark slides: max ~80 palavras (fundo escuro cansa mais rápido)
- Light slides: max ~100 palavras

---

## 3. Espaçamento — Regra do Terço Inferior

O conteúdo textual ocupa o **terço inferior e médio** do slide (`flex-end`). O terço superior fica como "respiro visual".

**Exceções onde o topo é preenchido:**
- Slide com `.img-box` no topo
- Slide com `.dark-big-stat` (número gigante)
- Slide de capa (imagem full-bleed)
- Slide com headline interna grande (80px+ preenche naturalmente)

**Se o slide parece "vazio" mesmo com flex-end:**
1. Primeiro: aumentar o font-size do body ou da headline
2. Segundo: adicionar um card (`.dark-card` ou `.light-card`)
3. Terceiro: sugerir um `.img-box`
4. Último recurso: adicionar mais conteúdo

---

## 4. Tipografia — Escala e Contraste

### Escala fixa (1080×1350px nativos)

| Elemento | Tamanho | Peso | Uso |
|----------|---------|------|-----|
| Headline capa | 88–108px | 900 | Capa do carrossel |
| Headline interna dark | 72–80px | 900 | Slides dark com título |
| Headline interna light | 64–72px | 900 | Slides light com título |
| Headline gradient | 72–80px | 900 | Slide gradient |
| Body | 36–40px | 400 | Texto corrido |
| Body strong | 36–40px | 700–800 | Destaques dentro do body |
| Tag | 13px | 700 | Labels de seção |
| Brand bar | 14–17px | 700 | Topo de cada slide |
| Progress counter | 15px | 600 | Rodapé |

### Regras de cor do texto
- Dark slides: body em `rgba(255,255,255,0.55)`, strong em `#fff`, accent em `var(--PL)`
- Light slides: body em `rgba(15,13,12,0.60)`, strong em `var(--DB)`, accent em `var(--P)`
- Accent (cor primária) apenas em **palavras-chave**, nunca em frases inteiras

---

## 5. Componentes Visuais — Quando Usar Cada Um

### Card (`.dark-card` / `.light-card`)
**Usar quando:** o texto precisa de destaque extra, citação, ou é uma lista de 2-3 itens.
**Não usar quando:** o slide já tem headline + body (card vira ruído).

### Tabela (`.light-table`)
**Usar quando:** slide de dados com 3+ itens comparáveis.
**Não usar quando:** slide com menos de 3 dados.

### Big Stat (`.dark-big-stat`)
**Usar quando:** um único número é o protagonista do slide (ex: "2.300%").
**Não usar quando:** o slide tem múltiplos dados de peso igual.

### Image Box (`.img-box`)
**Usar quando:** slide tem <60% de preenchimento textual E usuário tem imagem disponível.
**Não usar quando:** slide já está denso ou imagem não adiciona informação.

### Arrow Rows (`.dark-arrow-row` / `.grad-row`)
**Usar quando:** slide lista 2-3 pontos sequenciais.
**Não usar quando:** mais de 4 itens (vira lista, perde impacto).

---

## 6. Geração de Paleta a partir de Uma Cor

```
BRAND_PRIMARY = cor informada pelo usuário
BRAND_LIGHT  = primary clareado ~20% (mix com branco)
BRAND_DARK   = primary escurecido ~30% (mix com preto)
LIGHT_BG     = off-white com temperatura do primary
                warm (vermelho, laranja, amarelo) → #F5F2EF
                cool (azul, verde, roxo)          → #F0F2F5
DARK_BG      = near-black com leve tint
                warm → #0F0D0C
                cool → #0C0D10
GRADIENT     = linear-gradient(165deg, BRAND_DARK 0%, BRAND_PRIMARY 50%, BRAND_LIGHT 100%)
```

**Regra de contraste:** a cor primária NUNCA aparece como fundo de texto. Sempre como accent em palavras-chave, borda de card, fill de progress bar.

---

## 7. Sequência Padrão (9 slides)

| Slide | Função | Background |
|-------|--------|-----------|
| 1 | Capa | Foto full-bleed + gradiente escuro |
| 2 | Hook | Dark |
| 3 | Contexto/Mecanismo pt.1 | Light |
| 4 | Mecanismo pt.2 | Dark |
| 5 | Prova/Dados | Light |
| 6 | Expansão | Dark |
| 7 | Aplicação | Light |
| 8 | Direção | Gradient |
| 9 | CTA | Light |

**Adaptação por número de slides:**

5 slides: Capa | Hook+Contexto (Dark) | Prova (Light) | Aplicação+Direção (Dark) | CTA (Light)

7 slides: Capa | Hook (Dark) | Mecanismo (Light) | Prova (Dark) | Expansão (Light) | Direção (Grad) | CTA (Light)

12 slides: Capa | Hook (Dark) | Contexto (Light) | Mec.1 (Dark) | Mec.2 (Light) | Prova (Dark) | Dados (Light) | Expansão (Dark) | Caso (Light) | Aplicação (Dark) | Direção (Grad) | CTA (Light)

---

## 8. Slide de Capa — Regras

- Foto full-bleed com gradiente escuro pesado na base
- Badge do handle: alinhado à esquerda, dentro do bloco headline-area
- SEM badge de tipo/data na capa — a capa é limpa, só foto + headline + handle
- Headline: usar a headline **COMPLETA** escolhida, uppercase, fonte condensada, palavras-chave em BRAND_PRIMARY
- Só encurtar se não couber em 5 linhas a 88px
- Badge + headline ficam num bloco único posicionado no terço inferior (bottom: 120px)
- Nenhum texto fora da área safe (52px horizontal, 80px embaixo)

**Derivação CORRETA de headline para capa:**
- Headline: "A morte do corredor solitário: como os clubes viraram a nova balada dos adultos brasileiros" → Capa: USA INTEIRA (cabe em 4 linhas)
- Headline longa: encurtar mantendo o padrão original (se tinha dois-pontos, a versão curta também tem)

**Derivação ERRADA:**
- ❌ Headline boa → "A NOVA BALADA COMEÇA ÀS 6H" (matou o dois-pontos e o hook)
- ❌ Headline boa → "O CLUBE QUE TOMOU AS RUAS" (virou declaração genérica)

---

## 9. CTA — Regras

- Frase-ponte é OBRIGATÓRIA. Conecta o último insight do carrossel ao CTA.
- Nunca CTA genérico desconectado do conteúdo.
- Layout alinhado à esquerda, nunca centralizado.
- Sem swipe arrow — o swipe é nativo do Instagram.

---

## 10. Checklist Visual — Rodar Antes de Renderizar

Para CADA slide do carrossel:

1. ☐ Hierarquia de 3 níveis clara (âncora, contexto, metadata)
2. ☐ Contraste texto/fundo ≥ 4.5:1
3. ☐ Accent color apenas em palavras-chave, não em frases
4. ☐ Safe area respeitada (56px horizontal, 80px bottom)
5. ☐ Nenhum elemento sobrepõe progress bar ou brand bar
6. ☐ Headline não ultrapassa 4 linhas no tamanho definido
7. ☐ Alternância dark/light respeitada (nunca 3 seguidos do mesmo)
8. ☐ Componente visual correto pro conteúdo (card, tabela, stat, img-box)
9. ☐ Sem swipe arrow
10. ☐ CTA tem frase-ponte conectando conteúdo ao call-to-action

---

## 11. Anti-patterns Visuais — Nunca Fazer

- ❌ Texto centralizado em slides de conteúdo
- ❌ Dois parágrafos do mesmo tamanho/peso sem diferenciação
- ❌ Imagem sem overlay suficiente comprometendo legibilidade
- ❌ Cor accent em mais de 3 palavras por slide
- ❌ Card dentro de card
- ❌ Tabela com menos de 3 linhas
- ❌ Headline em sentence case (sempre uppercase em condensada)
- ❌ Body text em uppercase (nunca)
- ❌ Mais de 100 palavras em um slide dark
- ❌ Slide com apenas tag + 1 frase curta (parece incompleto)
