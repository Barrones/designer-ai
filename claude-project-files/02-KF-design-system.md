# Designer AI — Design System (Knowledge File)

> Especificação completa de CSS/HTML para o sistema de carrosséis.
> Todos os slides: 1080 × 1350 px (proporção 4:5 Instagram).

---

## 1. Variáveis CSS

```css
:root {
  /* === CORES (configuradas por briefing) === */
  --P:   #1A3A6B;          /* Primary — cor principal da marca */
  --PL:  #E8EEF6;          /* Primary Light — fundo claro */
  --PD:  #0D1F3C;          /* Primary Dark — fundo escuro */
  --LB:  #F5F5F5;          /* Light Background — slides claros */
  --LR:  #F0F0F0;          /* Light Relief — cards em slide claro */
  --DB:  #111111;           /* Dark Background — slides escuros */
  --G:   linear-gradient(135deg, var(--P), var(--PD)); /* Gradiente */

  /* === TIPOGRAFIA === */
  --F-HEAD: 'Sora', sans-serif;    /* Fonte headlines */
  --F-BODY: 'Sora', sans-serif;    /* Fonte body */

  /* === TAMANHOS === */
  --slide-w: 1080px;
  --slide-h: 1350px;
  --pad: 64px;                     /* Padding lateral padrão */
  --pad-top: 48px;                 /* Padding topo (abaixo da accent bar) */
  --pad-bot: 72px;                 /* Padding base (acima da brand bar) */
  --accent-h: 4px;                 /* Altura accent bar */
  --brand-h: 40px;                 /* Altura brand bar */
  --progress-h: 8px;               /* Altura progress bar */
  --radius: 16px;                  /* Border radius padrão */
  --radius-sm: 8px;                /* Border radius pequeno */

  /* === SOMBRAS === */
  --shadow-card: 0 4px 24px rgba(0,0,0,0.08);
  --shadow-card-dark: 0 4px 24px rgba(0,0,0,0.3);
}
```

---

## 2. Base / Reset

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.slide {
  position: relative;
  width: var(--slide-w);
  height: var(--slide-h);
  overflow: hidden;
  font-family: var(--F-BODY);
}
```

---

## 3. Accent Bar

Barra fina no topo de TODOS os slides.

```css
.accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: var(--accent-h);
  background: var(--P);
  z-index: 10;
}
```

---

## 4. Brand Bar

Rodapé com "Powered by Designer AI" em TODOS os slides.

```css
.brand-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: var(--brand-h);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--F-BODY);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.5;
  z-index: 10;
}

.slide.dark .brand-bar,
.slide.dark-img .brand-bar,
.slide.gradient .brand-bar,
.slide.cover .brand-bar,
.slide.cta .brand-bar { color: rgba(255,255,255,0.5); }

.slide.light .brand-bar { color: rgba(0,0,0,0.35); }
```

**Texto fixo:** `Powered by Designer AI`

---

## 5. Progress Bar

Indicador de progresso entre accent bar e conteúdo.

```css
.progress-bar {
  position: absolute;
  top: calc(var(--accent-h) + 16px);
  left: var(--pad);
  right: var(--pad);
  display: flex;
  gap: 6px;
  z-index: 10;
}

.progress-dot {
  flex: 1;
  height: var(--progress-h);
  border-radius: 4px;
  background: rgba(255,255,255,0.2);
  transition: background 0.3s;
}

.progress-dot.active {
  background: var(--P);
}

/* Em slides claros */
.slide.light .progress-dot {
  background: rgba(0,0,0,0.1);
}
.slide.light .progress-dot.active {
  background: var(--P);
}
```

---

## 6. Tag / Label

```css
.tag {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 100px;
  font-family: var(--F-BODY);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.tag-primary {
  background: var(--P);
  color: #FFFFFF;
}

.tag-outline {
  background: transparent;
  border: 1.5px solid var(--P);
  color: var(--P);
}

.tag-ghost {
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
}
```

---

## 7. Content Area

Área de conteúdo usa flex-end para empurrar conteúdo para a parte inferior do slide (regra do terço inferior).

```css
.slide-content {
  position: absolute;
  top: calc(var(--accent-h) + var(--progress-h) + 40px);
  left: var(--pad);
  right: var(--pad);
  bottom: calc(var(--brand-h) + 16px);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 20px;
  z-index: 5;
}
```

---

## 8. Slide — Capa (Cover)

Imagem full-bleed com gradiente overlay, badge e headline.

```css
.slide.cover {
  background: var(--DB);
}

.cover-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.cover-gradient {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,0.1) 0%,
    rgba(0,0,0,0.3) 40%,
    rgba(0,0,0,0.85) 75%,
    rgba(0,0,0,0.95) 100%
  );
  z-index: 2;
}

.cover-badge {
  display: inline-block;
  padding: 8px 20px;
  background: var(--P);
  color: #FFFFFF;
  font-family: var(--F-BODY);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border-radius: 100px;
  margin-bottom: 16px;
}

.cover-headline {
  font-family: var(--F-HEAD);
  font-size: 58px;
  font-weight: 800;
  line-height: 1.1;
  color: #FFFFFF;
  max-width: 90%;
}

.cover-subtitle {
  font-family: var(--F-BODY);
  font-size: 22px;
  font-weight: 400;
  color: rgba(255,255,255,0.75);
  line-height: 1.4;
  margin-top: 12px;
}
```

**Quando não há imagem de capa** — usar gradiente sólido:
```css
.slide.cover.no-image {
  background: var(--G);
}
```

---

## 9. Slide — Dark

Fundo escuro, ghost number, headline, body, com suporte a card, arrows e big stat.

```css
.slide.dark {
  background: var(--DB);
  color: #FFFFFF;
}

.ghost-number {
  position: absolute;
  top: 60px;
  right: -20px;
  font-family: var(--F-HEAD);
  font-size: 280px;
  font-weight: 900;
  color: rgba(255,255,255,0.03);
  line-height: 1;
  z-index: 1;
  user-select: none;
}

.slide-headline {
  font-family: var(--F-HEAD);
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
}

.slide.dark .slide-headline { color: #FFFFFF; }
.slide.light .slide-headline { color: var(--PD); }

.slide-body {
  font-family: var(--F-BODY);
  font-size: 24px;
  font-weight: 400;
  line-height: 1.55;
}

.slide.dark .slide-body { color: rgba(255,255,255,0.85); }
.slide.light .slide-body { color: rgba(0,0,0,0.75); }

/* Card em slide dark */
.card-dark {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius);
  padding: 28px 32px;
  margin-top: 16px;
}

.card-dark .card-title {
  font-family: var(--F-HEAD);
  font-size: 26px;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 8px;
}

.card-dark .card-body {
  font-family: var(--F-BODY);
  font-size: 20px;
  color: rgba(255,255,255,0.7);
  line-height: 1.5;
}

/* Arrow rows */
.arrow-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 8px 0;
}

.arrow-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--P);
  border-radius: 50%;
  color: #FFF;
  font-size: 16px;
  flex-shrink: 0;
}

.arrow-text {
  font-family: var(--F-BODY);
  font-size: 22px;
  color: rgba(255,255,255,0.85);
  line-height: 1.4;
}

/* Big stat */
.big-stat {
  font-family: var(--F-HEAD);
  font-size: 84px;
  font-weight: 900;
  color: var(--P);
  line-height: 1;
  margin-bottom: 8px;
}

.big-stat-label {
  font-family: var(--F-BODY);
  font-size: 22px;
  color: rgba(255,255,255,0.6);
  font-weight: 400;
}
```

---

## 10. Slide — Light

Fundo claro, com suporte a card, pattern card e table.

```css
.slide.light {
  background: var(--LB);
  color: var(--PD);
}

/* Card em slide light */
.card-light {
  background: #FFFFFF;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: var(--radius);
  padding: 28px 32px;
  box-shadow: var(--shadow-card);
  margin-top: 16px;
}

.card-light .card-title {
  font-family: var(--F-HEAD);
  font-size: 26px;
  font-weight: 600;
  color: var(--PD);
  margin-bottom: 8px;
}

.card-light .card-body {
  font-family: var(--F-BODY);
  font-size: 20px;
  color: rgba(0,0,0,0.65);
  line-height: 1.5;
}

/* Pattern card (card com borda lateral colorida) */
.pattern-card {
  background: #FFFFFF;
  border-left: 4px solid var(--P);
  border-radius: 0 var(--radius) var(--radius) 0;
  padding: 24px 28px;
  box-shadow: var(--shadow-card);
  margin: 8px 0;
}

.pattern-card .pattern-label {
  font-family: var(--F-BODY);
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--P);
  margin-bottom: 6px;
}

.pattern-card .pattern-value {
  font-family: var(--F-HEAD);
  font-size: 22px;
  font-weight: 600;
  color: var(--PD);
}

/* Table em slide light */
.slide-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 16px;
}

.slide-table th {
  background: var(--P);
  color: #FFFFFF;
  font-family: var(--F-BODY);
  font-size: 15px;
  font-weight: 600;
  padding: 14px 20px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.slide-table td {
  background: #FFFFFF;
  font-family: var(--F-BODY);
  font-size: 19px;
  padding: 14px 20px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  color: var(--PD);
}

.slide-table tr:nth-child(even) td {
  background: var(--LR);
}
```

---

## 11. Slide — Gradient

```css
.slide.gradient {
  background: var(--G);
  color: #FFFFFF;
}

.slide.gradient .slide-headline { color: #FFFFFF; }
.slide.gradient .slide-body { color: rgba(255,255,255,0.85); }
```

---

## 12. Slide — Dark com Imagem (Overlay)

Imagem de fundo com overlay escuro de 70%+ opacidade.

```css
.slide.dark-img {
  color: #FFFFFF;
}

.slide-bg-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.slide-bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.75);
  z-index: 2;
}

.slide.dark-img .slide-content { z-index: 3; }
.slide.dark-img .accent-bar { z-index: 4; }
.slide.dark-img .brand-bar { z-index: 4; }
.slide.dark-img .progress-bar { z-index: 4; }
```

---

## 13. Image Box Component

Componente para inserir imagem dentro de um slide (não full-bleed).

```css
.img-box {
  width: 100%;
  border-radius: var(--radius);
  overflow: hidden;
  margin: 16px 0;
  position: relative;
}

.img-box img {
  width: 100%;
  height: 280px;
  object-fit: cover;
  display: block;
}

.img-box-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 20px;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  font-family: var(--F-BODY);
  font-size: 14px;
  color: rgba(255,255,255,0.8);
}
```

---

## 14. Slide — CTA

Último slide com frase-ponte, keyword box e footer.

```css
.slide.cta {
  background: var(--G);
  color: #FFFFFF;
}

.cta-bridge {
  font-family: var(--F-BODY);
  font-size: 26px;
  font-weight: 400;
  color: rgba(255,255,255,0.8);
  line-height: 1.5;
  margin-bottom: 24px;
}

.cta-keyword-box {
  background: rgba(255,255,255,0.12);
  border: 1.5px solid rgba(255,255,255,0.2);
  border-radius: var(--radius);
  padding: 32px;
  text-align: center;
  margin-bottom: 24px;
}

.cta-keyword {
  font-family: var(--F-HEAD);
  font-size: 40px;
  font-weight: 800;
  color: #FFFFFF;
  line-height: 1.2;
}

.cta-action {
  font-family: var(--F-BODY);
  font-size: 20px;
  color: rgba(255,255,255,0.7);
  margin-top: 12px;
}

.cta-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
}

.cta-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--P);
  border: 2px solid rgba(255,255,255,0.3);
}

.cta-handle {
  font-family: var(--F-BODY);
  font-size: 18px;
  font-weight: 600;
  color: #FFFFFF;
}

.cta-label {
  font-family: var(--F-BODY);
  font-size: 14px;
  color: rgba(255,255,255,0.6);
}
```

---

## 15. Sequência de Slides (Alternância Dark/Light)

| Qtd Slides | Sequência |
|------------|-----------|
| 5 | cover → dark → light → dark → cta |
| 7 | cover → dark → light → dark → light → dark → cta |
| 9 | cover → dark → light → dark → light → dark → light → dark → cta |
| 12 | cover → dark → light → dark → light → dark → light → dark → light → dark → light → cta |

**Regra:** Slide após a capa é SEMPRE dark. Slide antes do CTA é SEMPRE dark. Alternância estrita no miolo.

---

## 16. Garantias de Legibilidade

| Regra | Critério |
|-------|----------|
| Contraste mínimo texto/fundo (dark) | WCAG AA — ratio ≥ 4.5:1 |
| Contraste mínimo texto/fundo (light) | WCAG AA — ratio ≥ 4.5:1 |
| Overlay mínimo em imagens | 70% opacidade |
| Tamanho mínimo de corpo | 20px |
| Tamanho mínimo de metadado | 13px |
| Espaçamento mínimo entre linhas (body) | 1.45 |
| Máximo de palavras por slide | 60 (exceto capa e CTA) |
| Máximo de linhas de corpo por slide | 6 |

---

## 17. Preview Mode

Visualização lado a lado (miniatures) + toggle para tamanho real.

```css
/* Container de preview */
.preview-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px;
  background: #1A1A1A;
  justify-content: center;
}

/* Miniatura */
.preview-thumb {
  width: 200px;
  height: 250px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border 0.2s, transform 0.2s;
}

.preview-thumb:hover {
  border-color: var(--P);
  transform: scale(1.03);
}

.preview-thumb .slide {
  transform: scale(0.1852);  /* 200/1080 */
  transform-origin: top left;
}

/* Slide label na miniatura */
.preview-label {
  text-align: center;
  font-family: var(--F-BODY);
  font-size: 12px;
  color: rgba(255,255,255,0.6);
  margin-top: 6px;
}

/* Toggle full size */
.preview-full {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.9);
  z-index: 1000;
  justify-content: center;
  align-items: center;
  cursor: zoom-out;
}

.preview-full.active { display: flex; }

.preview-full .slide {
  transform: scale(0.65);
  box-shadow: 0 0 80px rgba(0,0,0,0.5);
}
```

---

## 18. Instagram Frame Preview

Simula como o slide aparece no feed do Instagram (com header e action bar).

```css
.ig-frame {
  width: 400px;
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 32px rgba(0,0,0,0.12);
}

.ig-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
}

.ig-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--P);
}

.ig-username {
  font-family: -apple-system, sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.ig-post-image {
  width: 400px;
  height: 500px;   /* 400 * 1.25 */
  overflow: hidden;
}

.ig-post-image .slide {
  transform: scale(0.3704);  /* 400/1080 */
  transform-origin: top left;
}

.ig-actions {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
}

.ig-action-icon {
  width: 24px;
  height: 24px;
  color: #262626;
}
```

---

## 19. Estrutura HTML Completa (Template)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carrossel — Designer AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    /* [Inserir todas as variáveis e CSS acima] */
  </style>
</head>
<body>
  <div class="preview-container">

    <!-- SLIDE 1: COVER -->
    <div class="slide cover">
      <div class="accent-bar"></div>
      <div class="progress-bar">
        <div class="progress-dot active"></div>
        <div class="progress-dot"></div>
        <!-- ... -->
      </div>
      <img class="cover-image" src="[URL]" alt="">
      <div class="cover-gradient"></div>
      <div class="slide-content">
        <span class="cover-badge">[Nicho/Tag]</span>
        <h1 class="cover-headline">[Headline]</h1>
        <p class="cover-subtitle">[Subtítulo opcional]</p>
      </div>
      <div class="brand-bar">Powered by Designer AI</div>
    </div>

    <!-- SLIDE 2: DARK -->
    <div class="slide dark">
      <div class="accent-bar"></div>
      <div class="progress-bar"><!-- dots --></div>
      <span class="ghost-number">02</span>
      <div class="slide-content">
        <h2 class="slide-headline">[Título interno]</h2>
        <p class="slide-body">[Corpo do texto]</p>
      </div>
      <div class="brand-bar">Powered by Designer AI</div>
    </div>

    <!-- SLIDE 3: LIGHT -->
    <div class="slide light">
      <div class="accent-bar"></div>
      <div class="progress-bar"><!-- dots --></div>
      <div class="slide-content">
        <h2 class="slide-headline">[Título interno]</h2>
        <p class="slide-body">[Corpo do texto]</p>
        <div class="card-light">
          <div class="card-title">[Card título]</div>
          <div class="card-body">[Card corpo]</div>
        </div>
      </div>
      <div class="brand-bar">Powered by Designer AI</div>
    </div>

    <!-- SLIDE N: CTA -->
    <div class="slide cta">
      <div class="accent-bar"></div>
      <div class="progress-bar"><!-- dots --></div>
      <div class="slide-content">
        <p class="cta-bridge">[Frase-ponte]</p>
        <div class="cta-keyword-box">
          <div class="cta-keyword">[Palavra-chave / CTA]</div>
          <div class="cta-action">[Instrução de ação]</div>
        </div>
        <div class="cta-footer">
          <div class="cta-avatar"></div>
          <div>
            <div class="cta-handle">@[perfil]</div>
            <div class="cta-label">[Label]</div>
          </div>
        </div>
      </div>
      <div class="brand-bar">Powered by Designer AI</div>
    </div>

  </div>
</body>
</html>
```

---

## 20. Notas de Implementação

1. **Fontes como base64** — Se o carrossel precisa funcionar 100% offline, converter as fontes para base64 e embutir no `<style>` via `@font-face { src: url(data:font/woff2;base64,...) }`.
2. **Google Fonts** — Alternativa mais simples. Usar `<link>` no `<head>`. Requer internet.
3. **Imagens** — Podem ser base64 inline (`src="data:image/jpeg;base64,..."`) ou URLs externas.
4. **Export** — O HTML é projetado para ser exportado via Playwright (ver script na Etapa 5.5 do prompt).
5. **Responsividade** — NÃO é necessária. O carrossel é fixo em 1080×1350px.
