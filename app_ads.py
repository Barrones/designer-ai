"""
Designer AI — Gerador de HTML5 Ads (Google Display)
Interface standalone para criar banners animados.

Rodar:
    uv run streamlit run app_ads.py --server.port 8502
"""
import io
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="HTML5 Ads — Designer AI", page_icon="📦", layout="centered")

st.markdown("""
<style>
body, .stApp { background-color: #0D0D14; color: #FFFFFF; }
section[data-testid="stSidebar"] { display: none; }
.stApp > header { display: none; }
h1 { font-size: 28px; font-weight: 900; letter-spacing: -1px; margin-bottom: 4px; }
h3 { font-size: 11px; font-weight: 700; color: #555; text-transform: uppercase;
     letter-spacing: 2px; margin-top: 28px; margin-bottom: 10px; }
.block {
    background: #13131C; border: 1px solid #222230; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 14px;
}
.size-card {
    background: #13131C; border: 1px solid #2A2A3A; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px; font-size: 13px; color: #CCC;
}
.size-card.active { border-color: #00D4FF; background: #00D4FF10; }
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF, #0088CC); color: #000;
    font-weight: 800; font-size: 15px; border-radius: 12px; padding: 14px;
    border: none; width: 100%;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #13131C !important; color: #FFF !important;
    border: 1px solid #2A2A3A !important; border-radius: 10px !important;
}
div[data-testid="stSelectbox"] > div { background: #13131C; border: 1px solid #2A2A3A; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Imports do módulo ─────────────────────────────────────────────────────────
from designer.delivery.html5_ads import SIZES, DEFAULT_SIZES, generate_html5_pack
from designer.copy.headlines import CopyResult

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "brand_profiles")

NICHE_OPTIONS = {
    "🏦 Finanças / Crédito": "finance",
    "💻 Tecnologia / SaaS": "tech",
    "🛍️ E-commerce / Moda": "ecommerce",
    "🏠 Premium / Imobiliário": "premium",
    "📦 Padrão (genérico)": "default",
}

LANG_OPTIONS = {
    "🇧🇷 Português": "pt",
    "🇺🇸 English": "en",
    "🇪🇸 Español": "es",
}


def list_brands():
    if not os.path.exists(PROFILES_DIR):
        return []
    return [f.stem for f in sorted(Path(PROFILES_DIR).glob("*.json"))]


def load_brand_json(slug):
    import json
    with open(os.path.join(PROFILES_DIR, f"{slug}.json")) as f:
        return json.load(f)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📦 HTML5 Ads Generator")
st.markdown(
    "<p style='color:#555;margin-top:-10px;margin-bottom:24px'>"
    "Gere banners HTML5 animados para Google Display Network — prontos para subir."
    "</p>",
    unsafe_allow_html=True,
)

# ── Marca ─────────────────────────────────────────────────────────────────────
st.markdown("### Marca")
brands = list_brands()
use_brand = st.toggle("Usar perfil salvo", value=bool(brands), key="use_brand")

if use_brand and brands:
    chosen = st.selectbox("Marca", brands, label_visibility="collapsed")
    bd = load_brand_json(chosen)
    brand_name = bd["client_name"]
    accent = bd.get("color_palette", {}).get("accent", "#00D4FF")
    niche_val = bd.get("niche", "")
    st.markdown(
        f"<div class='block'><b>{brand_name}</b> &nbsp;"
        f"<span style='color:#555;font-size:13px'>{bd.get('subniche', '')}</span>"
        f"<div style='display:inline-block;width:16px;height:16px;border-radius:50%;"
        f"background:{accent};vertical-align:middle;margin-left:10px'></div></div>",
        unsafe_allow_html=True,
    )
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        brand_name = st.text_input("Nome da marca", placeholder="Ex: FitPro")
    with col2:
        accent = st.color_picker("Cor destaque", "#00D4FF")
    niche_val = ""

# ── Headlines ─────────────────────────────────────────────────────────────────
st.markdown("### Headlines")
col_h1, col_h2 = st.columns(2)
with col_h1:
    headline1 = st.text_input("Headline 1 (atenção)", placeholder="Ex: Crédito aprovado em 5 minutos")
with col_h2:
    headline2 = st.text_input("Headline 2 (benefício)", placeholder="Ex: Sem burocracia, 100% digital")

# ── CTA & Config ──────────────────────────────────────────────────────────────
st.markdown("### Configuração")
col_c, col_l, col_n = st.columns(3)
with col_c:
    cta = st.text_input("CTA (botão)", value="Saiba mais")
with col_l:
    lang_label = st.selectbox("Idioma", list(LANG_OPTIONS.keys()))
    lang = LANG_OPTIONS[lang_label]
with col_n:
    niche_label = st.selectbox("Nicho", list(NICHE_OPTIONS.keys()))
    niche = NICHE_OPTIONS[niche_label]

if use_brand and niche_val:
    # Tenta detectar nicho do perfil salvo
    niche_lower = niche_val.lower()
    for label, val in NICHE_OPTIONS.items():
        if val in niche_lower or niche_lower in val:
            niche = val
            break

if not use_brand:
    accent = st.session_state.get("accent", accent)

# ── Formatos ──────────────────────────────────────────────────────────────────
st.markdown("### Formatos")
all_sizes = st.toggle("Todos os 14 formatos", value=False)

if not all_sizes:
    SIZE_LABELS = {
        k: f"{v[0]}×{v[1]}" for k, v in SIZES.items()
    }
    SIZE_CATEGORIES = {
        "Retângulos": ["square_250", "rectangle", "large_rectangle"],
        "Skyscrapers": ["skyscraper", "half_page", "portrait"],
        "Leaderboards": ["banner_468", "leaderboard", "large_leaderboard", "billboard", "slim_billboard"],
        "Mobile": ["mobile_banner", "mobile_banner_lg", "mobile_inter"],
    }

    selected_sizes = []
    for cat_name, cat_sizes in SIZE_CATEGORIES.items():
        st.markdown(f"<span style='color:#666;font-size:11px'>{cat_name.upper()}</span>", unsafe_allow_html=True)
        cols = st.columns(len(cat_sizes))
        for i, size_key in enumerate(cat_sizes):
            w, h = SIZES[size_key]
            is_default = size_key in DEFAULT_SIZES
            with cols[i]:
                checked = st.checkbox(
                    f"{w}×{h}",
                    value=is_default,
                    key=f"sz_{size_key}",
                )
                if checked:
                    selected_sizes.append(size_key)
else:
    selected_sizes = list(SIZES.keys())

st.markdown(f"<span style='color:#00D4FF;font-size:12px'>✓ {len(selected_sizes)} formatos selecionados</span>", unsafe_allow_html=True)

# ── Gerar ─────────────────────────────────────────────────────────────────────
st.markdown("")
gerar = st.button("⚡ Gerar Banners HTML5", type="primary", use_container_width=True)

if gerar:
    if not headline1.strip() or not headline2.strip():
        st.error("Preencha as duas headlines.")
        st.stop()
    if not selected_sizes:
        st.error("Selecione ao menos um formato.")
        st.stop()

    copy = CopyResult(
        formula="direct",
        headline_part1=headline1,
        headline_part2=headline2,
        caption="",
        hashtags=[],
        image_query="",
        video_query="",
        compliance_flags=[],
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", f"html5_{ts}")

    with st.status(f"📦 Gerando {len(selected_sizes)} banners HTML5...", expanded=True) as status:
        zips = generate_html5_pack(
            copy_result=copy,
            brand_name=brand_name or "Brand",
            niche=niche,
            accent_color=accent,
            cta_text=cta,
            output_dir=output_dir,
            sizes=selected_sizes,
            lang=lang,
        )
        status.update(label=f"✅ {len(zips)} banners gerados!", state="complete")

    # ── Resultado ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.success(f"✅ {len(zips)} banners HTML5 prontos!")

    # Mostra lista de ZIPs gerados
    for zip_path in zips:
        fname = os.path.basename(zip_path)
        fsize = os.path.getsize(zip_path)
        # Extrai dimensão do nome
        st.markdown(
            f"<div class='size-card'>"
            f"📄 <b>{fname}</b> &nbsp; <span style='color:#00D4FF'>{fsize / 1024:.1f} KB</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Download all como ZIP único ───────────────────────────────────────
    st.markdown("### Download")

    # Empacota todos os ZIPs num ZIP único para download
    mega_zip_buf = io.BytesIO()
    with zipfile.ZipFile(mega_zip_buf, "w", zipfile.ZIP_DEFLATED) as mega:
        for zip_path in zips:
            mega.write(zip_path, os.path.basename(zip_path))
    mega_zip_buf.seek(0)

    slug = (brand_name or "ads").lower().replace(" ", "-")
    st.download_button(
        label=f"⬇️ Baixar tudo ({len(zips)} banners)",
        data=mega_zip_buf,
        file_name=f"html5_ads_{slug}_{ts}.zip",
        mime="application/zip",
        use_container_width=True,
    )

    # Download individual
    with st.expander("📁 Download individual"):
        for zip_path in zips:
            with open(zip_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ {os.path.basename(zip_path)}",
                    data=f,
                    file_name=os.path.basename(zip_path),
                    mime="application/zip",
                    key=f"dl_{os.path.basename(zip_path)}",
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#333;font-size:11px;padding:10px'>"
    "Designer AI 1.0 · HTML5 Ads Generator · Google Display Network Compliant"
    "</div>",
    unsafe_allow_html=True,
)
