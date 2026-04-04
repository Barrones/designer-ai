"""
Designer AI — Interface Web
Fluxo: nome + nicho + país → IA pesquisa tudo → gera conteúdo.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from pathlib import Path as _Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# ---------------------------------------------------------------------------
st.set_page_config(page_title="Designer AI", page_icon="🎨", layout="centered")

st.markdown("""
<style>
body, .stApp { background-color: #0D0D14; color: #FFFFFF; }
section[data-testid="stSidebar"] { display: none; }
.stApp > header { display: none; }

h1 { font-size: 30px; font-weight: 900; letter-spacing: -1px; margin-bottom: 4px; }
h3 { font-size: 11px; font-weight: 700; color: #555; text-transform: uppercase;
     letter-spacing: 2px; margin-top: 32px; margin-bottom: 10px; }

.block {
    background: #13131C;
    border: 1px solid #222230;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 14px;
}
.tag {
    display: inline-block;
    background: #1E1E30;
    color: #AAA;
    border: 1px solid #333;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    margin: 3px 3px 3px 0;
    cursor: pointer;
}
.tag-accent {
    background: #00D4FF18;
    color: #00D4FF;
    border-color: #00D4FF44;
}
.pain-item {
    background: #1A1020;
    border-left: 3px solid #FF4466;
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin-bottom: 6px;
    font-size: 14px;
    color: #EEE;
}
.trend-item {
    background: #0D1A20;
    border-left: 3px solid #00D4FF;
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin-bottom: 6px;
    font-size: 14px;
    color: #EEE;
}
.topic-btn {
    background: #1A1A2E;
    border: 1px solid #333355;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #CCC;
    cursor: pointer;
    width: 100%;
    text-align: left;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF, #0088CC);
    color: #000;
    font-weight: 800;
    font-size: 15px;
    border-radius: 12px;
    padding: 14px;
    border: none;
    width: 100%;
}
div[data-testid="stButton"] > button:not([kind="primary"]) {
    background: #1A1A2E;
    color: #AAA;
    border: 1px solid #333;
    border-radius: 8px;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #13131C !important;
    color: #FFF !important;
    border: 1px solid #2A2A3A !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] > div { background: #13131C; border: 1px solid #2A2A3A; border-radius: 10px; }
.stRadio > div { gap: 8px; }
.stRadio label { background: #13131C; border: 1px solid #2A2A3A; border-radius: 8px; padding: 8px 14px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
PROFILES_DIR = os.path.join(os.path.dirname(__file__), "brand_profiles")
COUNTRIES = {
    "🇧🇷 Brasil": "BR", "🇺🇸 EUA": "US", "🇮🇹 Itália": "IT",
    "🇪🇸 Espanha": "ES", "🇩🇪 Alemanha": "DE", "🇫🇷 França": "FR",
    "🇲🇽 México": "MX", "🇵🇹 Portugal": "PT", "🇬🇧 Reino Unido": "UK",
}

def list_brands():
    if not os.path.exists(PROFILES_DIR): return []
    return [f.stem for f in sorted(Path(PROFILES_DIR).glob("*.json"))]

def load_brand(slug):
    with open(os.path.join(PROFILES_DIR, f"{slug}.json")) as f:
        return json.load(f)

def save_brand(data):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(os.path.join(PROFILES_DIR, f"{data['slug']}.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown("# 🎨 Designer AI")
st.markdown("<p style='color:#555;margin-top:-10px;margin-bottom:24px'>Conteúdo de alto impacto gerado por IA.</p>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# STEP 1 — MARCA
# ---------------------------------------------------------------------------
st.markdown("### Marca")

brands = list_brands()
use_saved = st.toggle("Usar marca salva", value=bool(brands), key="use_saved")

if use_saved and brands:
    chosen = st.selectbox("", brands, label_visibility="collapsed")
    bd = load_brand(chosen)
    brand_slug   = bd["slug"]
    brand_name   = bd["client_name"]
    brand_niche  = bd["subniche"]
    intel_loaded = bd  # usamos o JSON salvo como intel

    accent = bd.get("color_palette", {}).get("accent", "#00D4FF")
    pains  = bd.get("audience", {}).get("pains", [])
    trends = bd.get("trends", [])
    topic_suggestions = bd.get("topic_suggestions", [])

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{brand_name}** &nbsp; <span style='color:#555;font-size:13px'>{brand_niche}</span>", unsafe_allow_html=True)
        if pains:
            st.markdown("Dores identificadas:")
            for p in pains[:4]:
                st.markdown(f"<div class='pain-item'>🔴 {p}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='width:40px;height:40px;border-radius:50%;background:{accent};margin:auto'></div>", unsafe_allow_html=True)

    intel = None  # já carregado do JSON

else:
    col1, col2, col3 = st.columns([2, 3, 2])
    with col1:
        brand_name = st.text_input("Nome da marca", placeholder="Ex: FitPro")
    with col2:
        brand_niche = st.text_input("Nicho / produto", placeholder="Ex: suplementos para ganho de massa muscular")
    with col3:
        country_label = st.selectbox("País", list(COUNTRIES.keys()), key="country_intel")
        country = COUNTRIES[country_label]

    pesquisar = st.button("🔍 Pesquisar tendências e dores", use_container_width=True)

    intel = st.session_state.get("intel")
    brand_slug = brand_name.lower().replace(" ", "-").replace("/", "-") if brand_name else ""

    if pesquisar and brand_name and brand_niche:
        with st.spinner(f"Pesquisando {brand_niche} em {country_label}..."):
            from designer.research.brand_intel import research_brand
            intel = research_brand(brand_name=brand_name, niche=brand_niche, country=country)
            st.session_state["intel"] = intel
            st.session_state["brand_name"]  = brand_name
            st.session_state["brand_niche"] = brand_niche
            st.session_state["country"]     = country

    if intel:
        # Resultado da pesquisa
        col_t, col_p = st.columns(2)

        with col_t:
            st.markdown("**Tendências do nicho**")
            for t in intel.trends[:4]:
                st.markdown(f"<div class='trend-item'>📈 {t}</div>", unsafe_allow_html=True)

        with col_p:
            st.markdown("**Dores do público**")
            for p in intel.pains[:5]:
                st.markdown(f"<div class='pain-item'>🔴 {p}</div>", unsafe_allow_html=True)

        st.markdown(f"**Tom de voz recomendado:** {intel.tone}")

        # Salvar marca com dados pesquisados
        if st.button("💾 Salvar esta marca", key="save_new"):
            save_brand({
                "slug": brand_slug,
                "client_name": brand_name,
                "niche": brand_niche.split("/")[0].strip(),
                "subniche": brand_niche,
                "product": brand_niche,
                "goal": f"Criar conteúdo de alto impacto para {brand_niche}",
                "tone": intel.tone,
                "content_pillars": intel.pillars,
                "content_angles": intel.angles,
                "suggested_formats": ["carrossel", "reels"],
                "trends": intel.trends,
                "topic_suggestions": intel.topic_suggestions,
                "audience": {
                    "description": intel.audience_description,
                    "age_range": "25-45",
                    "pains": intel.pains,
                    "desires": intel.desires,
                    "language": intel.audience_language,
                },
                "color_palette": {
                    "primary": "#0A1628",
                    "secondary": "#1E3A5F",
                    "accent": intel.accent_color,
                    "text": "#FFFFFF",
                },
                "handle": f"@{brand_slug}",
                "created_at": datetime.now().isoformat(),
            })
            st.success(f"✅ {brand_name} salva!")
            st.rerun()

        topic_suggestions = intel.topic_suggestions
        accent = intel.accent_color
    else:
        topic_suggestions = []
        accent = "#00D4FF"

# ---------------------------------------------------------------------------
# STEP 2 — CONTEÚDO
# ---------------------------------------------------------------------------
st.markdown("### Conteúdo")

# Sugestões de temas clicáveis
if topic_suggestions:
    st.markdown("<span style='color:#666;font-size:12px'>SUGESTÕES — CLIQUE PARA SELECIONAR</span>", unsafe_allow_html=True)
    for i, suggestion in enumerate(topic_suggestions[:5]):
        selected = st.session_state.get("topic_input", "") == suggestion
        label = f"✅ {suggestion}" if selected else f"💡 {suggestion}"
        if st.button(label, key=f"topic_{i}", use_container_width=True):
            st.session_state["topic_input"] = suggestion
            st.rerun()

topic = st.text_area(
    "Tema do post",
    placeholder="Clique numa sugestão acima ou escreva o seu tema",
    height=80,
    key="topic_input",
)

# ── CRIADOR DE REFERÊNCIA ────────────────────────────────────────────────
st.markdown("### Voz do Criador *(opcional)*")

try:
    from designer.research.creator_style import list_creators
    _available_creators = list_creators()
except Exception:
    _available_creators = []

if _available_creators:
    _creator_options = ["— Sem referência —"] + _available_creators
    _creator_choice = st.selectbox(
        "Adaptar linguagem ao estilo de um criador",
        _creator_options,
        key="creator_select",
        help="A IA vai escrever a legenda com a voz deste criador, adaptada ao nicho da marca.",
    )
    selected_creator = None if _creator_choice == "— Sem referência —" else _creator_choice
else:
    selected_creator = None
    st.caption("Nenhum criador disponível — adicione vídeos ao projeto Agente de IA.")

# ---------------------------------------------------------------------------
col_a, col_b = st.columns([2, 1])
with col_a:
    cta = st.text_input("Call to Action", placeholder="Ex: Solicite agora", value="Saiba mais")
with col_b:
    if not use_saved:
        country_label2 = st.selectbox("País", list(COUNTRIES.keys()), key="country_gen")
        country = COUNTRIES[country_label2]
    content_type = st.radio("Tipo", ["🖼️ Carrossel", "🎬 Vídeo", "📦 Ambos"], horizontal=True)

if "Vídeo" in content_type:
    duration = st.slider("Duração do vídeo (seg)", 8, 30, 15)
else:
    duration = 15

# ---------------------------------------------------------------------------
# GERAR
# ---------------------------------------------------------------------------
st.markdown("")
gerar = st.button("⚡ Gerar Conteúdo", type="primary", use_container_width=True)

if gerar:
    if not topic.strip():
        st.error("Escolha ou escreva um tema.")
        st.stop()
    if not brand_name:
        st.error("Informe a marca.")
        st.stop()

    # Garante que o perfil existe em disco
    brand_json_path = os.path.join(PROFILES_DIR, f"{brand_slug}.json")
    if not os.path.exists(brand_json_path):
        if intel:
            save_brand({
                "slug": brand_slug,
                "client_name": brand_name,
                "niche": brand_niche.split("/")[0].strip(),
                "subniche": brand_niche,
                "product": brand_niche,
                "goal": f"Criar conteúdo de alto impacto para {brand_niche}",
                "tone": intel.tone,
                "content_pillars": intel.pillars,
                "content_angles": intel.angles,
                "suggested_formats": ["carrossel", "reels"],
                "trends": intel.trends,
                "topic_suggestions": intel.topic_suggestions,
                "audience": {
                    "description": intel.audience_description,
                    "age_range": "25-45",
                    "pains": intel.pains,
                    "desires": intel.desires,
                    "language": intel.audience_language,
                },
                "color_palette": {
                    "primary": "#0A1628",
                    "secondary": "#1E3A5F",
                    "accent": intel.accent_color,
                    "text": "#FFFFFF",
                },
                "handle": f"@{brand_slug}",
                "created_at": datetime.now().isoformat(),
            })
        else:
            st.error("Pesquise as tendências antes de gerar.")
            st.stop()

    from designer.brand.profile import BrandProfile
    brand = BrandProfile.load(brand_slug)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", f"{brand_slug}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    drive_urls = []

    st.markdown("---")

    # ── COPY ──────────────────────────────────────────────────────────────
    with st.status("✍️ Gerando copy com Claude...", expanded=False) as s:
        from designer.copy.headlines import generate as gen_copy

        _creator_style_obj = None
        if selected_creator:
            st.write(f"🎙️ Extraindo estilo de {selected_creator}...")
            from designer.research.creator_style import extract_creator_style
            _creator_style_obj = extract_creator_style(selected_creator)

        copy = gen_copy(topic=topic, brand=brand, creator_style=_creator_style_obj)
        creator_label = f" · estilo {selected_creator}" if selected_creator else ""
        s.update(label=f"✅ Copy gerado — Fórmula {copy.formula}{creator_label}", state="complete")

    st.markdown(f"""
    <div class='block'>
        <div style='color:#555;font-size:11px;letter-spacing:1px;margin-bottom:8px'>HEADLINE · Fórmula {copy.formula}</div>
        <div style='font-size:22px;font-weight:900;line-height:1.2;color:#FFF'>{copy.headline_part1}</div>
        <div style='font-size:19px;font-weight:700;line-height:1.2;color:{accent};margin-top:4px'>{copy.headline_part2}</div>
    </div>
    """, unsafe_allow_html=True)

    if copy.compliance_flags:
        for flag in copy.compliance_flags:
            st.warning(f"⚠️ Compliance: {flag}")

    # ── CARROSSEL ──────────────────────────────────────────────────────────
    if "Carrossel" in content_type or "Ambos" in content_type:
        with st.status("🖼️ Criando carrossel...", expanded=True) as s:
            from designer.image.unsplash import get_image_url
            from designer.visual.carousel import render_cover
            from designer.copy.slides import generate_slides
            from designer.visual.slide_renderer import render_slide

            st.write(f"🔍 Buscando imagem: *{copy.image_query}*")
            image_source = get_image_url(copy.image_query, topic=topic)

            carousel_dir = os.path.join(output_dir, "carousel")
            os.makedirs(carousel_dir, exist_ok=True)
            handle = brand.handle or f"@{brand_slug}"
            accent_rgb = brand.accent_rgb()

            cover_path = os.path.join(carousel_dir, "01_capa.png")
            render_cover(
                headline_part1=copy.headline_part1,
                headline_part2=copy.headline_part2,
                handle=handle,
                image_source=image_source,
                accent_color=accent_rgb,
                powered_by="Designer AI",
                year=datetime.now().year,
                output_path=cover_path,
            )
            st.write("✅ Capa gerada")

            st.write("🤖 Gerando slides com Claude...")
            slides = generate_slides(topic=topic, brand=brand, copy=copy)
            slide_paths = [cover_path]
            for slide in slides:
                sp = os.path.join(carousel_dir, f"0{slide.number + 1}_{slide.type}.png")
                render_slide(slide=slide, accent_color=accent_rgb, handle=handle, output_path=sp)
                slide_paths.append(sp)
                st.write(f"✅ Slide {slide.number}: {slide.headline[:50]}")

            try:
                from designer.delivery.drive import upload_carousel as drive_up
                st.write("📤 Enviando para o Drive...")
                urls = drive_up(files=slide_paths, brand_slug=brand_slug, topic=topic, content_type="carrosséis")
                drive_urls.extend(urls)
            except Exception as e:
                st.warning(f"Drive: {e}")

            s.update(label=f"✅ Carrossel pronto — {len(slide_paths)} slides", state="complete")

        st.image(cover_path, use_container_width=True)

    # ── VÍDEO ──────────────────────────────────────────────────────────────
    if "Vídeo" in content_type or "Ambos" in content_type:
        with st.status("🎬 Criando vídeo Reel...", expanded=True) as s:
            from designer.video.pexels_video import get_best_video
            from designer.video.composer import render_video

            st.write(f"🔍 Buscando vídeo: *{copy.video_query}*")
            video_bg = get_best_video(
                image_query=copy.video_query,
                topic=topic,
                orientation="portrait",
                min_duration=duration,
                max_duration=30,
            )
            st.write(f"✅ Vídeo: {os.path.basename(video_bg)}")

            st.write("🎬 Renderizando overlay...")
            output_video = os.path.join(output_dir, "reel.mp4")
            render_video(
                video_path=video_bg,
                headline_part1=copy.headline_part1,
                headline_part2=copy.headline_part2,
                cta=cta,
                handle=brand.handle or f"@{brand_slug}",
                accent_color=brand.accent_rgb(),
                output_path=output_video,
                duration=duration,
            )

            try:
                from designer.delivery.drive import upload_carousel as drive_up
                st.write("📤 Enviando para o Drive...")
                urls = drive_up(files=[output_video], brand_slug=brand_slug, topic=topic, content_type="videos")
                drive_urls.extend(urls)
            except Exception as e:
                st.warning(f"Drive: {e}")

            s.update(label="✅ Vídeo pronto!", state="complete")

        st.video(output_video)

    # ── EXPORT GOOGLE ADS + META ADS ──────────────────────────────────────
    cover_for_ads = cover_path if "Carrossel" in content_type or "Ambos" in content_type else None
    video_for_ads = output_video if "Vídeo" in content_type or "Ambos" in content_type else None

    if cover_for_ads:
        with st.status("📦 Gerando pacote para Google Ads e Meta Ads...", expanded=False) as s:
            from designer.delivery.ads_export import export_ads_package
            ads = export_ads_package(
                cover_image_path=cover_for_ads,
                video_path=video_for_ads,
                copy_result=copy,
                brand_name=brand_name,
                output_dir=output_dir,
            )
            try:
                from designer.delivery.drive import upload_carousel as drive_up
                ads_files = [ads.report_path]
                for f in Path(ads.google_ads_dir).glob("*"):
                    ads_files.append(str(f))
                for f in Path(ads.meta_ads_dir).glob("*"):
                    ads_files.append(str(f))
                urls_ads = drive_up(files=ads_files, brand_slug=brand_slug, topic=topic + " — Ads", content_type="ads")
                drive_urls.extend(urls_ads)
            except Exception as e:
                st.warning(f"Drive ads: {e}")
            s.update(label="✅ Pacote de anúncios pronto!", state="complete")

    # ── RESULTADO ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.success("✅ Conteúdo gerado!")

    col_r1, col_r2 = st.columns([3, 2])
    with col_r1:
        st.markdown("**Legenda pronta para publicar**")
        st.text_area("", copy.caption, height=200, label_visibility="collapsed")
    with col_r2:
        st.markdown("**Hashtags**")
        st.markdown(" ".join(f"`{h}`" for h in copy.hashtags[:12]))
        if drive_urls:
            st.markdown("**Drive**")
            for url in drive_urls[:5]:
                st.markdown(f"[📁 Abrir no Drive]({url})")

    # ── COPY DE ADS ────────────────────────────────────────────────────────
    if cover_for_ads:
        st.markdown("---")
        tab_g, tab_m = st.tabs(["🔵 Google Ads", "🔷 Meta Ads"])

        with tab_g:
            st.markdown("**Headlines** (máx 30 chars)")
            for i, h in enumerate(ads.google_copy["headlines"], 1):
                st.markdown(f"`{i}.` {h} — *{len(h)} chars*")
            st.markdown("**Descriptions** (máx 90 chars)")
            for i, d in enumerate(ads.google_copy["descriptions"], 1):
                st.markdown(f"`{i}.` {d} — *{len(d)} chars*")
            if video_for_ads:
                st.info("📹 Vídeo: faça upload no YouTube primeiro, depois vincule no Google Ads como asset de vídeo.")
            st.warning(f"⚠️ {ads.google_copy['compliance_note']}")

        with tab_m:
            st.markdown(f"**Headline:** {ads.meta_copy['headline']} — *{len(ads.meta_copy['headline'])} chars*")
            st.markdown(f"**Primary Text:**")
            st.text_area("", ads.meta_copy["primary_text"], height=80, label_visibility="collapsed", key="meta_pt")
            st.markdown(f"**Description:** {ads.meta_copy['description']}")
            st.markdown(f"**Hashtags:** {ads.meta_copy['hashtags']}")
            if video_for_ads:
                st.info("📹 Vídeo: sobe direto no Gerenciador de Anúncios do Meta.")
            st.warning(f"⚠️ {ads.meta_copy['compliance_note']}")
