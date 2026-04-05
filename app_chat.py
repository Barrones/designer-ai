"""
Designer AI — Chat Interface (Content Machine Style)
Fluxo conversacional: boas-vindas → modo → briefing → pesquisa → headlines → texto → render
"""
import json
import os
import sys
import re
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from anthropic import Anthropic

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Designer AI", page_icon="🎨", layout="centered")

st.markdown("""
<style>
body, .stApp { background-color: #0D0D14; color: #FFFFFF; }
section[data-testid="stSidebar"] { display: none; }
.stApp > header { display: none; }
h1 { font-size: 26px; font-weight: 900; letter-spacing: -1px; }
.stChatMessage { background: #13131C !important; border: 1px solid #1E1E30 !important; border-radius: 14px !important; }
div[data-testid="stChatInput"] textarea { background: #13131C !important; color: #FFF !important; border: 1px solid #2A2A3A !important; }
</style>
""", unsafe_allow_html=True)

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "brand_profiles")

# ---------------------------------------------------------------------------
# LOAD SYSTEM PROMPT
# ---------------------------------------------------------------------------
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "designer", "prompts", "chat_system_prompt.md")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "designer", "knowledge")

@st.cache_data
def load_system_context():
    """Load system prompt + all knowledge files."""
    parts = []

    # System prompt
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, encoding="utf-8") as f:
            parts.append(f.read())

    # Knowledge files
    if os.path.exists(KNOWLEDGE_DIR):
        for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
            if fname.endswith(".md"):
                fpath = os.path.join(KNOWLEDGE_DIR, fname)
                with open(fpath, encoding="utf-8") as f:
                    parts.append(f"\n\n---\n# Knowledge: {fname}\n\n{f.read()}")

    # Also load the claude-project-files if available
    project_files_dir = os.path.join(os.path.dirname(__file__), "claude-project-files")
    if os.path.exists(project_files_dir):
        for fname in sorted(os.listdir(project_files_dir)):
            if fname.endswith(".md") and fname.startswith("0"):
                fpath = os.path.join(project_files_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    parts.append(f"\n\n---\n# {fname}\n\n{f.read()}")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "phase" not in st.session_state:
    st.session_state.phase = "welcome"  # welcome → mode → input → briefing → headlines → spine → text → images → render
if "carousel_data" not in st.session_state:
    st.session_state.carousel_data = {}


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown("# 🎨 Designer AI")

# ---------------------------------------------------------------------------
# CHAT DISPLAY
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# WELCOME (first load)
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    welcome = """Bem-vindo(a) ao **Designer AI | 5.5 Claude Edition** — sistema avançado de criação de carrosséis virais para Instagram.

Para qual intenção criativa vamos trabalhar agora:

1. Transformar um conteúdo existente em carrossel
2. Criar uma narrativa a partir de um insight

Responder apenas com **1** ou **2**."""

    st.session_state.messages.append({"role": "assistant", "content": welcome})
    st.session_state.phase = "mode"
    st.rerun()


# ---------------------------------------------------------------------------
# CLAUDE INTEGRATION (definidas antes de serem chamadas)
# ---------------------------------------------------------------------------

def _call_claude(user_message: str) -> str:
    """Send full conversation to Claude with system prompt."""
    client = Anthropic()
    system = load_system_context()

    messages = []
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=system,
        messages=messages,
    )

    return response.content[0].text


def _run_pipeline(briefing_text: str) -> str:
    """Parse briefing, research topic, generate headlines — all in one Claude call."""
    client = Anthropic()
    system = load_system_context()

    topic = st.session_state.carousel_data.get("input", "")
    mode = st.session_state.carousel_data.get("mode", 2)

    research_data = ""
    if mode == 2:
        try:
            from designer.research.topic_research import research_topic
            research = research_topic(topic)
            research_data = f"""
DADOS DA PESQUISA WEB:
Resumo: {research.resumo}
Dados: {chr(10).join(f'- {d}' for d in research.dados)}
Tendências: {chr(10).join(f'- {t}' for t in research.tendencias)}
Tensão central: {research.tensao_central}
Fontes: {', '.join(research.fontes)}
"""
        except Exception as e:
            research_data = f"[Pesquisa indisponível: {e}]"

    messages = []
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})

    enhanced_message = f"""{briefing_text}

{research_data}

INSTRUÇÃO INTERNA: O briefing foi recebido. Agora:
1. Parse as 7 respostas do briefing. Se faltar algo, peça APENAS o que falta.
2. Se tudo estiver completo, gere as 10 headlines usando os dados da pesquisa.
3. Apresente na tabela com Triagem, Eixo, Funil no topo."""

    messages.append({"role": "user", "content": enhanced_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=system,
        messages=messages,
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------------------------
user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    phase = st.session_state.phase
    response = ""

    if phase == "mode":
        if "1" in user_input:
            st.session_state.carousel_data["mode"] = 1
            response = "Cola aqui o conteúdo — link, texto, transcrição ou ideia — e eu cuido do resto."
            st.session_state.phase = "input"
        elif "2" in user_input:
            st.session_state.carousel_data["mode"] = 2
            response = "Me conta o insight, a ideia ou a observação que você quer transformar em carrossel."
            st.session_state.phase = "input"
        else:
            response = "Responder apenas com **1** ou **2**."

    elif phase == "input":
        st.session_state.carousel_data["input"] = user_input
        response = """Antes de criar, preciso de 7 coisas rápidas:

1. **Marca** — nome e @ do Instagram
2. **Nicho** — ex: marketing digital, fitness, imobiliário, gastronomia
3. **Cor principal** — hex (#E8421A) ou descrição ('laranja vibrante') — ou diz 'não sei' que eu sugiro
4. **Estilo visual** — A) Clássico B) Moderno C) Minimalista D) Bold E) Outro
5. **Tipo de carrossel** — A) Tendência Interpretada B) Tese Contraintuitiva C) Case/Benchmark D) Previsão/Futuro
6. **CTA do último slide** — ex: 'Comenta GUIA', 'Me segue', 'Salva esse post'
7. **Slides e imagens** — quantos slides (5/7/9/12) e em quantos deles você quer imagem (ex: '9 slides, 4 com imagem')"""
        st.session_state.phase = "briefing"

    elif phase == "briefing":
        st.session_state.carousel_data["briefing_raw"] = user_input
        with st.spinner("Pesquisando o tema e gerando headlines..."):
            response = _run_pipeline(user_input)
        st.session_state.phase = "headlines"

    else:
        with st.spinner("Processando..."):
            response = _call_claude(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
