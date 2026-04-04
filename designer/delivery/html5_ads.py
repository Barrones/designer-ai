"""
HTML5 Ad Generator — gera banners animados para Google Display Network / DV360.

Detecta o nicho e aplica o pack de efeitos certo:
  - Finanças/Crédito/Tech → loading bar + typing + cards
  - E-commerce           → zoom produto + preço fade + shine
  - Premium/Imobiliário  → parallax + reveal elegante
  - Padrão               → fade + slide + CTA pulse

Estrutura de cada banner (4 cenas):
  Cena 1: headline parte 1 (atenção)
  Cena 2: headline parte 2 (benefício)
  Cena 3: dado/prova (reforço)
  Cena 4: CTA pulsando (conversão)

Saída: {output_dir}/ads/google_display/html5_{W}x{H}.zip
"""
from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass


# ── Dimensões standard ──────────────────────────────────────────────────────
SIZES = {
    "rectangle":     (300, 250),
    "leaderboard":   (728, 90),
    "half_page":     (300, 600),
    "skyscraper":    (160, 600),
    "mobile_banner": (320, 50),
    "mobile_inter":  (320, 480),
}

# ── Detecção de nicho ────────────────────────────────────────────────────────
FINANCE_KEYWORDS = ["crédito", "financ", "banco", "cartão", "empréstimo", "score",
                    "credit", "loan", "bank", "finance", "invest", "money"]
TECH_KEYWORDS    = ["tech", "ia", "inteligência", "software", "app", "digital",
                    "ai", "technology", "platform", "saas"]
ECOMMERCE_KEYWORDS = ["moda", "roupa", "produto", "compra", "loja", "fashion",
                       "store", "shop", "style", "collection"]
PREMIUM_KEYWORDS = ["imóvel", "imobili", "luxo", "premium", "exclusive", "real estate"]


def _detect_niche(niche: str) -> str:
    niche_lower = niche.lower()
    if any(k in niche_lower for k in FINANCE_KEYWORDS):
        return "finance"
    if any(k in niche_lower for k in TECH_KEYWORDS):
        return "tech"
    if any(k in niche_lower for k in ECOMMERCE_KEYWORDS):
        return "ecommerce"
    if any(k in niche_lower for k in PREMIUM_KEYWORDS):
        return "premium"
    return "default"


# ── Gerador principal ────────────────────────────────────────────────────────

def generate_html5_pack(
    copy_result,
    brand_name: str,
    niche: str,
    accent_color: str,
    cta_text: str,
    output_dir: str,
    sizes: list[str] | None = None,
) -> list[str]:
    """
    Gera pack completo de banners HTML5 para Google Display.

    Parameters
    ----------
    copy_result   : CopyResult com headline_part1, headline_part2, caption
    brand_name    : nome da marca
    niche         : nicho (usado para detectar pack de efeitos)
    accent_color  : hex da cor de destaque (#00D4FF)
    cta_text      : texto do botão CTA
    output_dir    : pasta base de saída
    sizes         : lista de keys de SIZES (None = todos)

    Returns
    -------
    Lista de caminhos dos .zip gerados
    """
    niche_type  = _detect_niche(niche)
    target_sizes = {k: v for k, v in SIZES.items() if not sizes or k in sizes}
    out_dir = os.path.join(output_dir, "ads", "google_display")
    os.makedirs(out_dir, exist_ok=True)

    MAX_ZIP_BYTES = 150 * 1024  # 150 KB — limite recomendado Google Display

    zips = []
    for size_name, (W, H) in target_sizes.items():
        html = _build_html(
            W=W, H=H,
            headline1=copy_result.headline_part1,
            headline2=copy_result.headline_part2,
            brand_name=brand_name,
            cta_text=cta_text,
            accent=accent_color,
            niche_type=niche_type,
        )

        # Valida: sem links hardcoded (regra Google Display)
        _validate_no_hardcoded_links(html, f"{W}x{H}")

        zip_path = os.path.join(out_dir, f"html5_{W}x{H}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", html)

        # Valida tamanho do arquivo
        zip_size = os.path.getsize(zip_path)
        if zip_size > MAX_ZIP_BYTES:
            print(f"  ⚠️  html5_{W}x{H}.zip: {zip_size//1024}KB > 150KB recomendado")

        zips.append(zip_path)
        print(f"  ✓ html5_{W}x{H}.zip — {zip_size//1024}KB")

    return zips


def _validate_no_hardcoded_links(html: str, size: str) -> None:
    """
    Garante que o HTML5 não contém links hardcoded — regra obrigatória Google Display.
    Levanta erro se encontrar URL fixa fora do clickTag.
    """
    import re
    # Procura href="http ou src="http (exceto data:)
    bad_patterns = [
        r'href=["\']https?://',
        r'src=["\']https?://',
        r'window\.location\s*=\s*["\']https?://',
        r'window\.open\(["\']https?://',   # open com URL fixa (não variável)
    ]
    for pattern in bad_patterns:
        if re.search(pattern, html):
            raise ValueError(
                f"Banner {size}: link hardcoded detectado! "
                f"Use apenas 'var clickTag = \"\"' para URLs. "
                f"Pattern: {pattern}"
            )


# ── Builder de HTML ──────────────────────────────────────────────────────────

def _build_html(
    W: int, H: int,
    headline1: str, headline2: str,
    brand_name: str, cta_text: str,
    accent: str, niche_type: str,
) -> str:
    """Gera o HTML5 completo para um tamanho específico."""

    accent_dark = _darken(accent)
    is_horizontal = W > H * 1.5     # leaderboard, mobile banner
    is_small      = H <= 100         # leaderboard, mobile banner
    font_scale    = min(W, H) / 250  # escala relativa ao menor lado

    hl1_size = max(10, int(18 * font_scale))
    hl2_size = max(9,  int(15 * font_scale))
    cta_size = max(9,  int(13 * font_scale))
    brand_size = max(8, int(11 * font_scale))

    # Efeitos por nicho
    extra_css, extra_html, extra_js = _get_niche_effects(
        niche_type, accent, W, H, is_small
    )

    # Trunca textos para caber no banner
    h1 = _fit_text(headline1, W, hl1_size)
    h2 = _fit_text(headline2, W, hl2_size)
    cta = cta_text[:20].upper()
    brand = brand_name[:18]

    layout_css = _get_layout_css(W, H, is_horizontal, is_small)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="ad.size" content="width={W},height={H}">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    width:{W}px; height:{H}px;
    overflow:hidden; cursor:pointer;
    font-family:'Arial Black',Arial,sans-serif;
    background:#0A0A14;
}}

/* ── Cenas ── */
.scene {{
    position:absolute; width:100%; height:100%;
    display:flex; flex-direction:column;
    justify-content:center; align-items:center;
    padding:{max(6, int(H*0.05))}px {max(8, int(W*0.04))}px;
    opacity:0; pointer-events:none;
    transition:opacity 0.5s ease;
}}
.scene.active {{ opacity:1; pointer-events:auto; }}

/* ── Background gradient ── */
.bg {{
    position:absolute; inset:0;
    background:linear-gradient(135deg, #08080F 0%, #13132A 60%, #0A0A14 100%);
    z-index:0;
}}
.accent-bar {{
    position:absolute; top:0; left:0; right:0;
    height:{max(2, int(H*0.015))}px;
    background:linear-gradient(90deg, {accent}, {accent_dark});
    z-index:1;
}}

/* ── Textos ── */
.brand {{
    font-size:{brand_size}px; color:{accent};
    letter-spacing:2px; text-transform:uppercase;
    font-weight:400; opacity:0.8;
    font-family:Arial,sans-serif;
    z-index:2; margin-bottom:{max(4, int(H*0.02))}px;
}}
.headline1 {{
    font-size:{hl1_size}px; color:#FFFFFF;
    font-weight:900; text-align:center; line-height:1.1;
    text-transform:uppercase; z-index:2;
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
}}
.headline2 {{
    font-size:{hl2_size}px; color:{accent};
    font-weight:700; text-align:center; line-height:1.15;
    text-transform:uppercase; z-index:2; margin-top:{max(3,int(H*0.015))}px;
    text-shadow: 0 1px 6px rgba(0,0,0,0.6);
}}
.proof {{
    font-size:{max(8,int(hl2_size*0.8))}px; color:rgba(255,255,255,0.75);
    text-align:center; z-index:2; font-family:Arial,sans-serif;
    margin-top:{max(4,int(H*0.02))}px; line-height:1.3;
}}

/* ── CTA ── */
.cta-btn {{
    background:{accent};
    color:#000000; font-weight:900;
    font-size:{cta_size}px;
    border:none; border-radius:{max(3,int(H*0.06))}px;
    padding:{max(4,int(H*0.04))}px {max(10,int(W*0.08))}px;
    cursor:pointer; text-transform:uppercase;
    letter-spacing:1px; z-index:3; margin-top:{max(6,int(H*0.03))}px;
    box-shadow:0 2px 12px rgba(0,212,255,0.4);
    animation:ctaPulse 1.8s ease-in-out infinite;
}}
@keyframes ctaPulse {{
    0%,100% {{ transform:scale(1); box-shadow:0 2px 12px rgba(0,212,255,0.4); }}
    50% {{ transform:scale(1.04); box-shadow:0 4px 20px rgba(0,212,255,0.7); }}
}}
.cta-btn::after {{
    content:''; position:absolute; inset:0;
    background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,0.25) 50%,transparent 100%);
    border-radius:inherit;
    transform:translateX(-100%);
    animation:shine 3s ease-in-out infinite 1s;
}}
.cta-btn {{ position:relative; overflow:hidden; }}
@keyframes shine {{
    0%   {{ transform:translateX(-100%); }}
    40%  {{ transform:translateX(100%); }}
    100% {{ transform:translateX(100%); }}
}}

/* ── Entrada de texto ── */
.slide-in-left  {{ animation:slideLeft 0.6s ease forwards; }}
.slide-in-right {{ animation:slideRight 0.6s ease forwards; }}
.fade-up        {{ animation:fadeUp 0.7s ease forwards; }}
@keyframes slideLeft  {{ from{{opacity:0;transform:translateX(-30px)}} to{{opacity:1;transform:none}} }}
@keyframes slideRight {{ from{{opacity:0;transform:translateX(30px)}}  to{{opacity:1;transform:none}} }}
@keyframes fadeUp     {{ from{{opacity:0;transform:translateY(20px)}}  to{{opacity:1;transform:none}} }}

{layout_css}
{extra_css}
</style>
</head>
<body>
<div class="bg"></div>
<div class="accent-bar"></div>

<!-- Cena 1: Atenção -->
<div class="scene active" id="s1">
  <div class="brand">{brand}</div>
  <div class="headline1 slide-in-left">{h1}</div>
</div>

<!-- Cena 2: Benefício -->
<div class="scene" id="s2">
  <div class="brand">{brand}</div>
  <div class="headline1">{h1}</div>
  <div class="headline2 slide-in-right">{h2}</div>
</div>

<!-- Cena 3: Reforço / Nicho effect -->
<div class="scene" id="s3">
  {extra_html}
</div>

<!-- Cena 4: CTA -->
<div class="scene" id="s4">
  <div class="headline2 fade-up" style="margin-bottom:{max(6,int(H*0.02))}px">{h2}</div>
  <button class="cta-btn" onclick="window.open(clickTag,'_blank')">{cta}</button>
</div>

<script>
// Click tag obrigatório para Google DV360 / Display
var clickTag = "";

// Troca de cenas
var scenes = document.querySelectorAll('.scene');
var current = 0;
var timings = [2200, 2000, 2200, 0]; // ms por cena (0 = fica na última)

function nextScene() {{
    scenes[current].classList.remove('active');
    current = (current + 1) % scenes.length;
    scenes[current].classList.add('active');
    // Reinicia animações da cena
    scenes[current].querySelectorAll('[class*="slide-in"],[class*="fade-up"]').forEach(function(el) {{
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = '';
    }});
    if (timings[current] > 0) {{
        setTimeout(nextScene, timings[current]);
    }}
}}
setTimeout(nextScene, timings[0]);

// Click em qualquer lugar abre o clickTag
document.body.addEventListener('click', function() {{
    if (clickTag) window.open(clickTag, '_blank');
}});

{extra_js}
</script>
</body>
</html>"""


def _get_niche_effects(niche: str, accent: str, W: int, H: int, is_small: bool):
    """Retorna CSS, HTML e JS extras conforme o nicho detectado."""

    if is_small:
        # Banners pequenos: sem efeito extra, só texto limpo
        return "", f"""
  <div class="headline1" style="font-size:{max(8,int(H*0.35))}px">
    Clique e saiba mais
  </div>""", ""

    if niche == "finance":
        # Loading bar + análise simulada
        bar_h = max(3, int(H * 0.025))
        css = f"""
.loading-wrap {{ width:80%; z-index:2; text-align:center; }}
.loading-label {{
    font-size:{max(9, int(H*0.04))}px; color:rgba(255,255,255,0.7);
    font-family:Arial,sans-serif; margin-bottom:{max(4,int(H*0.02))}px;
}}
.loading-bar {{
    width:100%; height:{bar_h}px;
    background:rgba(255,255,255,0.1); border-radius:{bar_h}px; overflow:hidden;
}}
.loading-fill {{
    height:100%; width:0%; background:linear-gradient(90deg,{accent},{_darken(accent)});
    border-radius:{bar_h}px; transition:width 1.8s cubic-bezier(.4,0,.2,1);
}}
.loading-pct {{
    font-size:{max(10,int(H*0.045))}px; color:{accent};
    font-weight:700; margin-top:{max(3,int(H*0.015))}px;
}}"""
        html = f"""
  <div class="loading-wrap">
    <div class="loading-label">Analisando seu perfil...</div>
    <div class="loading-bar"><div class="loading-fill" id="lbar"></div></div>
    <div class="loading-pct" id="lpct">0%</div>
  </div>"""
        js = """
var lbar = document.getElementById('lbar');
var lpct = document.getElementById('lpct');
document.getElementById('s3').addEventListener('transitionend', function(){});
// Ativa loading quando cena 3 ficar ativa
var obs = new MutationObserver(function(muts){
    muts.forEach(function(m){
        if(m.target.id==='s3' && m.target.classList.contains('active')){
            lbar.style.width='82%';
            var p=0, iv=setInterval(function(){
                p=Math.min(p+2,82);
                lpct.textContent=p+'%';
                if(p>=82) clearInterval(iv);
            },36);
        }
    });
});
obs.observe(document.getElementById('s3'),{attributes:true,attributeFilter:['class']});"""
        return css, html, js

    elif niche == "ecommerce":
        # Shine no produto + preço
        css = f"""
.promo-badge {{
    background:{accent}; color:#000; font-weight:900;
    font-size:{max(12,int(H*0.07))}px; border-radius:50%;
    width:{max(50,int(H*0.22))}px; height:{max(50,int(H*0.22))}px;
    display:flex; align-items:center; justify-content:center;
    animation:badgePop 0.5s ease forwards, rotateBadge 8s linear infinite;
    z-index:2; margin-bottom:{max(4,int(H*0.02))}px;
}}
@keyframes badgePop {{ from{{transform:scale(0)}} to{{transform:scale(1)}} }}
@keyframes rotateBadge {{ from{{transform:rotate(0deg)}} to{{transform:rotate(360deg)}} }}
.promo-text {{ color:rgba(255,255,255,0.9); font-size:{max(9,int(H*0.04))}px;
    z-index:2; font-family:Arial,sans-serif; text-align:center; }}"""
        html = f"""
  <div class="promo-badge">%</div>
  <div class="promo-text">Oferta especial para você</div>"""
        js = ""
        return css, html, js

    elif niche == "tech":
        # Typing effect
        css = f"""
.typing-wrap {{ z-index:2; text-align:center; width:90%; }}
.typing-text {{
    font-size:{max(10,int(H*0.045))}px; color:{accent};
    font-family:'Courier New',monospace; font-weight:700;
    border-right:2px solid {accent};
    white-space:nowrap; overflow:hidden; width:0;
    animation:typing 1.8s steps(30) forwards, blink 0.7s step-end infinite;
}}
@keyframes typing {{ to{{width:100%}} }}
@keyframes blink   {{ 50%{{border-color:transparent}} }}"""
        html = """
  <div class="typing-wrap">
    <div class="typing-text" id="ttext">Solução inteligente...</div>
  </div>"""
        js = ""
        return css, html, js

    elif niche == "premium":
        # Reveal elegante
        css = f"""
.reveal-wrap {{ position:relative; width:85%; z-index:2; overflow:hidden; }}
.reveal-text {{
    font-size:{max(10,int(H*0.05))}px; color:#FFFFFF;
    font-weight:700; text-align:center; text-transform:uppercase;
    letter-spacing:3px; animation:reveal 1s ease forwards;
}}
@keyframes reveal {{
    from{{clip-path:inset(0 100% 0 0)}} to{{clip-path:inset(0 0% 0 0)}}
}}
.reveal-line {{
    height:1px; background:{accent};
    width:0; animation:lineGrow 1.2s ease 0.5s forwards;
    margin:8px auto;
}}
@keyframes lineGrow {{ to{{width:60%}} }}"""
        html = """
  <div class="reveal-wrap">
    <div class="reveal-line"></div>
    <div class="reveal-text">Exclusividade que você merece</div>
    <div class="reveal-line"></div>
  </div>"""
        js = ""
        return css, html, js

    else:
        # Default: dado/prova social simples
        css = f"""
.proof-wrap {{
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
    border-left:3px solid {accent}; border-radius:0 8px 8px 0;
    padding:{max(8,int(H*0.04))}px {max(10,int(W*0.04))}px;
    z-index:2; width:85%; animation:fadeUp 0.7s ease forwards;
}}
.proof-number {{
    font-size:{max(16,int(H*0.09))}px; color:{accent};
    font-weight:900; line-height:1;
}}
.proof-label {{
    font-size:{max(8,int(H*0.038))}px; color:rgba(255,255,255,0.7);
    font-family:Arial,sans-serif; margin-top:{max(2,int(H*0.01))}px;
}}"""
        html = """
  <div class="proof-wrap">
    <div class="proof-number">+10.000</div>
    <div class="proof-label">clientes atendidos</div>
  </div>"""
        js = ""
        return css, html, js


def _get_layout_css(W: int, H: int, is_horizontal: bool, is_small: bool) -> str:
    if is_small:
        return f"""
.scene {{ flex-direction:row; justify-content:space-between; padding:0 {int(W*0.03)}px; }}
.brand {{ display:none; }}
.headline1 {{ font-size:{max(9,int(H*0.38))}px; white-space:nowrap; }}
.headline2 {{ display:none; }}"""
    return ""


def _fit_text(text: str, width: int, font_size: int) -> str:
    """Trunca texto para caber aproximadamente no banner."""
    chars_per_line = max(8, int(width / (font_size * 0.6)))
    if len(text) > chars_per_line * 2:
        return text[:chars_per_line * 2 - 3] + "..."
    return text


def _darken(hex_color: str, factor: float = 0.7) -> str:
    """Escurece uma cor hex."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r * factor), int(g * factor), int(b * factor)
    )
