#!/usr/bin/env python3
"""
Designer AI — Agente Autônomo de Conteúdo
==========================================

Pipeline completo sem interação humana:
  1. Carrega perfil de marca
  2. Pesquisa tendências do nicho (se --topic não fornecido)
  3. Gera 10 headlines → escolhe a mais forte automaticamente
  4. Gera slides do carrossel (9 por padrão)
  5. Renderiza PNGs (Pillow)
  6. Gera legenda + hashtags
  7. Posta no Instagram via instagrapi
  8. Loga resultado em output/log.jsonl

Uso:
    python agent.py --brand force-protocol
    python agent.py --brand force-protocol --topic "creatina e hipertrofia"
    python agent.py --brand force-protocol --slides 7 --type tese
    python agent.py --list-brands
    python agent.py --brand force-protocol --dry-run   # gera tudo, não posta
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.request as _urllib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── ansi ─────────────────────────────────────────────────────────────────────
BOLD  = "\033[1m"
DIM   = "\033[2m"
RST   = "\033[0m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
CYAN  = "\033[96m"
SEP   = "─" * 60
SEP2  = "═" * 60


def _h(title: str) -> None:
    print(f"\n{SEP2}\n  {BOLD}{title}{RST}\n{SEP2}")

def _ok(msg: str) -> None:
    print(f"  {GREEN}✓{RST}  {msg}")

def _warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RST}  {msg}")

def _err(msg: str) -> None:
    print(f"  {RED}✗{RST}  {msg}")

def _step(msg: str) -> None:
    print(f"  {CYAN}→{RST}  {msg}")


# ── Importações pesadas (lazy para CLI rápido) ────────────────────────────────

def _load_brand(slug: str):
    from designer.brand.profile import BrandProfile
    try:
        return BrandProfile.load(slug)
    except FileNotFoundError:
        _err(f"Perfil '{slug}' não encontrado.")
        _step("Rode: python onboard.py")
        sys.exit(1)


def _pick_topic(brand) -> str:
    """Usa brand_intel para sugerir o melhor tema do momento."""
    _step("Pesquisando tendências do nicho para escolher tema...")
    try:
        from designer.research.brand_intel import research_brand
        intel = research_brand(
            brand_name=brand.client_name,
            niche=brand.subniche or brand.niche,
            country="BR",
        )
        if intel.topic_suggestions:
            topic = intel.topic_suggestions[0]
            _ok(f"Tema selecionado: {topic}")
            return topic
    except Exception as e:
        _warn(f"brand_intel falhou ({e}), usando fallback")

    # Fallback: usa o subniche como tema
    topic = f"Tendências de {brand.subniche or brand.niche} em {datetime.now().year}"
    _ok(f"Tema fallback: {topic}")
    return topic


def _score_headline(headline_option) -> int:
    """
    Pontua uma headline para escolha automática.
    Critérios: número de gatilhos emocionais + palavras de alta performance.
    """
    HIGH_PERF_WORDS = {
        "morte", "novo", "nova", "fim", "brasil", "investigando",
        "crise", "geração", "geracional", "instagram", "dado",
        "bilhões", "trilhões", "salário", "fraude", "segredo",
    }
    score = len(headline_option.triggers) * 10
    text_lower = headline_option.headline.lower()
    for w in HIGH_PERF_WORDS:
        if w in text_lower:
            score += 5
    # IC format com dois-pontos = estrutura correta
    if headline_option.format_type == "IC" and ":" in headline_option.headline:
        score += 8
    return score


def _build_carousel(brand, topic: str, n_slides: int, carousel_type: str, cta_text: str) -> dict:
    """
    Executa o pipeline completo de carrossel e retorna metadados.

    Returns
    -------
    dict com: output_dir, slide_paths, cover_path, caption, hashtags, headline
    """
    from designer.copy.headlines import generate_headlines, generate as generate_copy
    from designer.copy.slides import generate_carousel_slides
    from designer.copy.editorial_filter import quick_scan, validate_and_fix
    from designer.visual.carousel import render_cover
    from designer.visual.slide_renderer import render_slide
    from designer.visual.html_renderer import render_html
    from designer.image.unsplash import get_image_url

    palette = brand.designer_palette()
    accent  = brand.accent_rgb()
    handle  = brand.handle or f"@{brand.slug}"

    # 1 — Headlines
    _h("ETAPA 1 — HEADLINES")
    _step(f"Gerando 10 headlines para: {topic[:60]}")
    hl_result = generate_headlines(topic=topic, brand=brand)
    _ok(f"Triagem: {hl_result.triagem}")

    # Escolha automática da headline com maior pontuação
    scored = sorted(hl_result.headlines, key=_score_headline, reverse=True)
    headline_obj = scored[0]
    headline = headline_obj.headline
    _ok(f"Headline #{headline_obj.number} selecionada (score={_score_headline(headline_obj)})")
    print(f"\n  {BOLD}{headline}{RST}\n")

    # 2 — Slides
    _h("ETAPA 2 — SLIDES")
    _step(f"Gerando {n_slides} slides ({carousel_type})...")
    slides = generate_carousel_slides(
        topic=topic,
        brand=brand,
        headline=headline,
        n_slides=n_slides,
        carousel_type=carousel_type,
        cta_text=cta_text or "Comenta abaixo",
    )
    _ok(f"{len(slides)} slides gerados")

    # 3 — Validação editorial
    _h("ETAPA 3 — VALIDAÇÃO")
    all_texts = [t for s in slides for t in [s.body, s.body2] if t]
    issues = quick_scan(all_texts)
    if issues:
        _warn(f"{len(issues)} problemas de AI slop — corrigindo com Claude...")
        fixed_texts, result = validate_and_fix(all_texts, headline, max_retries=1)
        # Aplica textos corrigidos de volta
        text_idx = 0
        for s in slides:
            if s.body and text_idx < len(fixed_texts):
                s.body = fixed_texts[text_idx]; text_idx += 1
            if s.body2 and text_idx < len(fixed_texts):
                s.body2 = fixed_texts[text_idx]; text_idx += 1
        _ok(f"Corrigido — {result.total_issues} issues restantes")
    else:
        _ok("Sem AI slop detectado")

    # 4 — Imagem de capa
    _h("ETAPA 4 — IMAGEM")
    _step("Buscando imagem scroll-stop...")
    try:
        image_source = get_image_url(topic, topic=topic)
        _ok(f"Imagem: {str(image_source)[:70]}")
    except Exception as e:
        image_source = ""
        _warn(f"Sem imagem ({e}) — usando gradiente da marca")

    # 5 — Render
    _h("ETAPA 5 — RENDER PNGs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", "carousels", f"{brand.slug}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    font_headline = getattr(brand.typography, "headline", "Barlow Condensed")
    font_body     = getattr(brand.typography, "body",     "Plus Jakarta Sans")

    # HTML preview
    html_path = os.path.join(output_dir, "carousel.html")
    # cover_image para HTML: só passar se for arquivo local
    cover_for_html = image_source if (image_source and os.path.exists(str(image_source))) else None
    render_html(
        slides=slides, brand_name=brand.client_name, handle=handle,
        palette=palette, headline=headline,
        cover_image=cover_for_html,
        font_headline=font_headline, font_body=font_body,
        year=datetime.now().year, output_path=html_path,
    )

    # Capa PNG
    cover_path = os.path.join(output_dir, "01_capa.png")
    hl_split = headline.split(":", 1)
    render_cover(
        headline_part1=hl_split[0].strip(),
        headline_part2=hl_split[1].strip() if len(hl_split) > 1 else "",
        handle=handle,
        image_source=image_source or "gradient",
        accent_color=accent,
        powered_by="Designer AI",
        year=datetime.now().year,
        output_path=cover_path,
    )
    print(f"    {GREEN}✓{RST}  01_capa.png")

    # Slides internos
    slide_paths = [cover_path]
    for s in slides:
        if s.type == "capa":
            continue
        sp = os.path.join(output_dir, f"{s.number:02d}_{s.type}.png")
        try:
            render_slide(
                slide=s, accent_color=accent, handle=handle,
                palette=palette, total_slides=n_slides,
                brand_name=brand.client_name, year=datetime.now().year,
                output_path=sp,
            )
            slide_paths.append(sp)
            print(f"    {GREEN}✓{RST}  {s.number:02d}_{s.type}.png")
        except Exception as e:
            _warn(f"Slide {s.number} falhou: {e}")

    _ok(f"{len(slide_paths)} PNGs em {output_dir}/")

    # 6 — Legenda
    _h("ETAPA 6 — LEGENDA")
    _step("Gerando copy completo com Claude...")
    copy = generate_copy(topic=topic, brand=brand)
    caption_full = copy.caption
    hashtags = copy.hashtags
    _ok("Copy gerado")
    print(f"\n  {DIM}{caption_full[:200]}...{RST}\n")
    print(f"  Hashtags: {' '.join(hashtags[:8])}\n")

    # Salva metadados
    meta = {
        "brand": brand.slug,
        "topic": topic,
        "headline": headline,
        "triagem": hl_result.triagem,
        "eixo": hl_result.eixo,
        "funil": hl_result.funil,
        "carousel_type": carousel_type,
        "n_slides": n_slides,
        "caption": caption_full,
        "hashtags": hashtags,
        "slide_paths": slide_paths,
        "generated_at": timestamp,
    }
    with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return {
        "output_dir": output_dir,
        "slide_paths": slide_paths,
        "cover_path": cover_path,
        "caption": caption_full,
        "hashtags": hashtags,
        "headline": headline,
    }


# ── Approval gate (Discord + WhatsApp) ───────────────────────────────────────

def _request_approval(
    file_path: str,
    brand_slug: str,
    topic: str,
    caption: str = "",
    timeout_seconds: int = 300,
) -> bool:
    """
    Envia preview para Discord e WhatsApp em paralelo.
    Retorna True se qualquer um dos canais aprovar.
    Se nenhum canal estiver configurado, aprova automaticamente.
    """
    import threading

    discord_ok   = None
    whatsapp_ok  = None
    discord_cfg  = bool(os.getenv("DISCORD_BOT_TOKEN") and os.getenv("DISCORD_CHANNEL_ID"))
    whatsapp_cfg = bool(os.getenv("ZAPI_INSTANCE_ID") and os.getenv("ZAPI_TOKEN") and os.getenv("ZAPI_PHONE"))

    if not discord_cfg and not whatsapp_cfg:
        _warn("Nenhum canal de aprovação configurado — aprovação automática")
        return True

    results: dict = {}

    def _discord():
        try:
            from designer.delivery.discord_preview import send_for_approval
            results["discord"] = send_for_approval(
                file_path=file_path,
                brand_slug=brand_slug,
                topic=topic,
                caption=caption,
                timeout_seconds=timeout_seconds,
            )
        except Exception as e:
            _warn(f"Discord erro: {e}")
            results["discord"] = None

    def _whatsapp():
        try:
            from designer.delivery.whatsapp import send_for_approval as wa_approval
            results["whatsapp"] = wa_approval(
                file_path=file_path,
                brand_slug=brand_slug,
                topic=topic,
                caption=caption,
                timeout_seconds=timeout_seconds,
            )
        except Exception as e:
            _warn(f"WhatsApp erro: {e}")
            results["whatsapp"] = None

    threads = []
    if discord_cfg:
        t = threading.Thread(target=_discord, daemon=True)
        t.start()
        threads.append(t)
    if whatsapp_cfg:
        t = threading.Thread(target=_whatsapp, daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=timeout_seconds + 10)

    discord_ok  = results.get("discord")
    whatsapp_ok = results.get("whatsapp")

    # Aprovado se qualquer canal aprovou
    if discord_ok is True or whatsapp_ok is True:
        _ok("Conteúdo APROVADO ✅")
        return True

    # Se ambos configurados mas ambos rejeitaram
    if discord_ok is False or whatsapp_ok is False:
        _err("Conteúdo REJEITADO ❌")
        return False

    # Falha em todos os canais → aprovação automática
    _warn("Canais de aprovação sem resposta — aprovação automática")
    return True


# ── Instagram ─────────────────────────────────────────────────────────────────

def _post_instagram(slide_paths: list[str], caption: str, hashtags: list[str]) -> dict:
    """
    Posta carrossel no Instagram usando instagrapi.

    Retorna dict com: ok, id, code, type, error
    """
    from instagrapi import Client as IGClient
    from instagrapi.exceptions import LoginRequired

    username    = os.getenv("IG_USERNAME", "")
    password    = os.getenv("IG_PASSWORD", "")
    session_id  = os.getenv("IG_SESSION_ID", "")

    if not username:
        return {
            "ok": False,
            "error": "IG_USERNAME não configurado no .env",
        }

    # Monta legenda completa
    full_caption = caption
    if hashtags:
        full_caption += "\n\n" + " ".join(hashtags[:12])

    # Handler para desafio de segurança do Instagram (email ou SMS)
    def _challenge_handler(username: str, choice: int = 1) -> str:
        """Pede o código de verificação enviado pelo Instagram."""
        method = "email" if choice == 1 else "SMS"
        print(f"\n{YELLOW}⚠  Instagram enviou um código de verificação via {method}.{RST}")
        code = input(f"   Digite o código recebido: ").strip()
        return code

    def _2fa_handler(username: str) -> str:
        """Pede o código TOTP de autenticação de dois fatores."""
        print(f"\n{YELLOW}⚠  Instagram pediu código 2FA (autenticador).{RST}")
        code = input(f"   Digite o código do autenticador: ").strip()
        return code

    # Login
    session_path = Path(f"/tmp/ig_session_{username}.json")
    cl = IGClient()
    cl.delay_range = [2, 4]
    cl.challenge_code_handler = _challenge_handler
    cl.two_factor_handler = _2fa_handler

    _step("Autenticando no Instagram...")
    try:
        # Método 1: Session ID do browser (mais confiável — não aciona bloqueios de IP)
        if session_id:
            try:
                cl.login_by_sessionid(session_id)
                cl.dump_settings(session_path)
                _ok(f"Login via session ID: @{username}")
            except Exception as e:
                _warn(f"Session ID inválido ({e}) — tentando user/pass...")
                session_id = ""  # fallback para user/pass

        # Método 2: user/pass com sessão salva
        if not session_id:
            if not password:
                return {"ok": False, "error": "IG_PASSWORD não configurado. Configure IG_SESSION_ID ou IG_PASSWORD no .env"}

            if session_path.exists():
                try:
                    cl.load_settings(session_path)
                    cl.login(username, password)
                    cl.dump_settings(session_path)
                    _ok(f"Login (sessão reutilizada): @{username}")
                except Exception:
                    # Sessão corrompida — faz login fresco
                    session_path.unlink(missing_ok=True)
                    cl = IGClient()
                    cl.delay_range = [2, 4]
                    cl.challenge_code_handler = _challenge_handler
                    cl.two_factor_handler = _2fa_handler
                    cl.login(username, password)
                    cl.dump_settings(session_path)
                    _ok(f"Login (fresco): @{username}")
            else:
                cl.login(username, password)
                cl.dump_settings(session_path)
                _ok(f"Login: @{username}")
    except LoginRequired:
        session_path.unlink(missing_ok=True)
        cl = IGClient()
        cl.delay_range = [2, 4]
        cl.challenge_code_handler = _challenge_handler
        cl.two_factor_handler = _2fa_handler
        cl.login(username, password)
        cl.dump_settings(session_path)
        _ok(f"Login renovado: @{username}")
    except Exception as e:
        return {"ok": False, "error": f"Login falhou: {e}"}

    # Filtra apenas arquivos que existem
    valid_paths = [Path(p) for p in slide_paths if os.path.exists(p)]
    if not valid_paths:
        return {"ok": False, "error": "Nenhum PNG válido para postar"}

    _step(f"Postando {len(valid_paths)} imagens no Instagram...")

    try:
        if len(valid_paths) == 1:
            media = cl.photo_upload(valid_paths[0], full_caption)
            return {"ok": True, "id": str(media.pk), "code": media.code, "type": "single"}
        else:
            # Carrossel (álbum) — limite de 10 imagens no Instagram
            media = cl.album_upload(valid_paths[:10], full_caption)
            return {"ok": True, "id": str(media.pk), "code": media.code, "type": "carousel"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Video pipeline ────────────────────────────────────────────────────────────

def _run_video(brand: "BrandProfile", topic: str, cta_text: str, dry_run: bool) -> dict:
    """
    Pipeline de Reel: Pexels → MoviePy → Instagram.
    Usa creative_direction.video_reel do perfil da marca.
    """
    from designer.video.pexels_video import get_best_video
    from designer.video.composer import render_video
    from anthropic import Anthropic

    cd = getattr(brand, "creative_direction", {}) or {}
    vd = cd.get("video_reel", {})

    # Monta query de vídeo com direção criativa
    pexels_queries = vd.get("pexels_queries", [])
    scene_mood     = vd.get("scene_mood", topic)
    forbidden      = vd.get("forbidden_footage", [])
    min_dur        = vd.get("min_duration", 10)
    max_dur        = vd.get("max_duration", 20)

    # Gera copy do vídeo (headline em 2 partes + legenda)
    _h("ETAPA V1 — COPY DO VÍDEO")
    _step("Gerando copy com Claude...")

    client = Anthropic()
    forbidden_str = "\n".join(f"- {f}" for f in forbidden) if forbidden else "nenhuma restrição específica"
    pexels_str    = "\n".join(f"- {q}" for q in pexels_queries) if pexels_queries else f"- {topic}"

    copy_resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Crie copy para um Reel do Instagram (9:16, 15-20s) para a marca {brand.client_name}.

Tema: {topic}
Tom: {brand.tone}
Audiência: {brand.audience.description if hasattr(brand, 'audience') and brand.audience else ''}
Mood visual da cena: {scene_mood}

Formato de resposta (JSON puro, sem markdown):
{{
  "headline_part1": "frase de impacto (max 6 palavras, UPPERCASE)",
  "headline_part2": "complemento revelador (max 8 palavras, UPPERCASE)",
  "video_query": "melhor query em inglês para buscar o vídeo ideal no Pexels",
  "caption": "legenda completa do Instagram (3-4 parágrafos, tom direto)",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5", "#tag6", "#tag7", "#tag8"]
}}"""
        }]
    )

    try:
        copy = json.loads(copy_resp.content[0].text.strip())
    except Exception:
        import re
        match = re.search(r'\{.*\}', copy_resp.content[0].text, re.DOTALL)
        copy = json.loads(match.group()) if match else {}

    headline_part1 = copy.get("headline_part1", topic.upper()[:20])
    headline_part2 = copy.get("headline_part2", "")
    video_query    = copy.get("video_query", pexels_queries[0] if pexels_queries else topic)
    caption        = copy.get("caption", "")
    hashtags       = copy.get("hashtags", [])

    _ok(f"Headline: {headline_part1} / {headline_part2}")
    _ok(f"Query Pexels: {video_query}")

    # Busca vídeo
    _h("ETAPA V2 — VÍDEO DE FUNDO (PEXELS)")
    _step(f"Buscando vídeo: {video_query}")
    try:
        video_path = get_best_video(
            image_query=video_query,
            topic=topic,
            orientation="portrait",
            min_duration=min_dur,
            max_duration=max_dur,
        )
        _ok(f"Vídeo: {Path(video_path).name}")
    except Exception as e:
        return {"ok": False, "error": f"Vídeo não encontrado: {e}"}

    # Render
    _h("ETAPA V3 — RENDER MP4")
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir  = os.path.join("output", "videos", f"{brand.slug}_{timestamp}")
    output_path = os.path.join(output_dir, "reel.mp4")
    os.makedirs(output_dir, exist_ok=True)

    handle = getattr(brand, "handle", None) or f"@{brand.slug}"
    accent = brand.accent_rgb()

    _step("Renderizando 1080×1920...")
    try:
        render_video(
            video_path=video_path,
            headline_part1=headline_part1,
            headline_part2=headline_part2,
            cta=cta_text or "Saiba mais →",
            handle=handle,
            accent_color=accent,
            output_path=output_path,
            duration=15,
        )
        _ok(f"MP4 gerado: {output_path}")
    except Exception as e:
        return {"ok": False, "error": f"Render falhou: {e}"}

    # Salva meta
    meta = {
        "brand": brand.slug,
        "topic": topic,
        "headline_part1": headline_part1,
        "headline_part2": headline_part2,
        "caption": caption,
        "hashtags": hashtags,
        "video_path": output_path,
        "generated_at": timestamp,
    }
    with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    if dry_run:
        _h("ETAPA V4 — INSTAGRAM (DRY-RUN)")
        _warn("Postagem ignorada (--dry-run)")
        print(f"\n  {DIM}{caption[:200]}...{RST}")
        return {"ok": True, "dry_run": True, "output_dir": output_dir, "video_path": output_path}

    # Aprovação
    _h("ETAPA V4 — APROVAÇÃO")
    approved = _request_approval(
        file_path=output_path,
        brand_slug=brand.slug,
        topic=topic,
        caption=caption,
    )
    if not approved:
        return {"ok": False, "error": "rejeitado na aprovação", "output_dir": output_dir, "video_path": output_path}

    # Posta no Instagram
    _h("ETAPA V5 — INSTAGRAM")
    ig = _post_instagram(
        slide_paths=[output_path],
        caption=caption,
        hashtags=hashtags,
    )
    if ig.get("ok"):
        _ok(f"Postado! https://instagram.com/p/{ig['code']}/")
    else:
        _err(f"Falha: {ig.get('error')}")

    return {"ok": ig.get("ok", False), "output_dir": output_dir, "video_path": output_path, "instagram": ig}


# ── Log ───────────────────────────────────────────────────────────────────────

def _log(entry: dict) -> None:
    """Appenda entrada no log geral (output/log.jsonl)."""
    os.makedirs("output", exist_ok=True)
    with open("output/log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Pipeline principal ────────────────────────────────────────────────────────

def run(
    brand_slug: str,
    topic: str = "",
    n_slides: int = 9,
    carousel_type: str = "tendencia",
    cta_text: str = "",
    dry_run: bool = False,
    fmt: str = "carousel",  # carousel | video | both
) -> None:
    """
    Agente autônomo completo.

    fmt="carousel" → carrossel PNG (padrão)
    fmt="video"    → Reel MP4 (Pexels + MoviePy, direção criativa do perfil)
    fmt="both"     → carrossel + vídeo

    dry_run=True   → gera tudo mas NÃO posta.
    """
    started_at = datetime.now().isoformat()

    _h("DESIGNER AI — AGENTE AUTÔNOMO")
    print(f"  Marca:   {brand_slug}")
    print(f"  Formato: {fmt.upper()}")
    if fmt == "carousel":
        print(f"  Slides:  {n_slides}  |  Tipo: {carousel_type}")
    if dry_run:
        print(f"  {YELLOW}Modo DRY-RUN — conteúdo será gerado mas NÃO postado{RST}")
    print()

    # 1 — Marca
    brand = _load_brand(brand_slug)
    _ok(f"Marca: {brand.client_name} ({brand.subniche or brand.niche})")

    # Imprime direção criativa ativa
    cd = getattr(brand, "creative_direction", None)
    if cd:
        fmt_key = "video_reel" if fmt == "video" else "carousel"
        mood = cd.get(fmt_key, {}).get("mood") or cd.get(fmt_key, {}).get("scene_mood", "")
        if mood:
            print(f"  {DIM}Direção criativa: {mood}{RST}\n")

    # 2 — Tema
    if not topic:
        topic = _pick_topic(brand)

    # 3a — Carrossel
    if fmt in ("carousel", "both"):
        result = _build_carousel(brand, topic, n_slides, carousel_type, cta_text)

        ig_result: dict = {"ok": False, "error": "dry-run"}
        if not dry_run:
            _h("ETAPA 7 — APROVAÇÃO")
            first_slide = result["slide_paths"][0] if result["slide_paths"] else ""
            approved = _request_approval(
                file_path=first_slide,
                brand_slug=brand_slug,
                topic=topic,
                caption=result["caption"],
            )
            if approved:
                _h("ETAPA 8 — INSTAGRAM (CARROSSEL)")
                ig_result = _post_instagram(
                    slide_paths=result["slide_paths"],
                    caption=result["caption"],
                    hashtags=result["hashtags"],
                )
                if ig_result.get("ok"):
                    _ok(f"Postado! https://instagram.com/p/{ig_result['code']}/")
                else:
                    _err(f"Falha: {ig_result.get('error')}")
            else:
                ig_result = {"ok": False, "error": "rejeitado na aprovação"}
                _warn("Postagem cancelada — conteúdo não aprovado")
        else:
            _h("ETAPA 7 — INSTAGRAM (DRY-RUN)")
            _warn("Postagem ignorada (--dry-run)")
            caption_preview = result["caption"]
            for line in caption_preview.split("\n")[:6]:
                print(f"    {line}")
            print(f"\n  Hashtags: {' '.join(result['hashtags'][:10])}")

        _log({
            "ts": started_at, "brand": brand_slug, "format": "carousel",
            "topic": topic, "headline": result["headline"],
            "output_dir": result["output_dir"],
            "n_slides": len(result["slide_paths"]),
            "dry_run": dry_run, "instagram": ig_result,
        })

        _h("CONCLUÍDO — CARROSSEL")
        print(f"  Pasta:    {result['output_dir']}/")
        print(f"  Slides:   {len(result['slide_paths'])} PNGs")
        print(f"  Headline: {result['headline'][:65]}...")
        if ig_result.get("ok"):
            print(f"  Instagram: {GREEN}https://instagram.com/p/{ig_result['code']}/{RST}")
        elif dry_run:
            print(f"  Instagram: {YELLOW}não postado (dry-run){RST}")
        else:
            print(f"  Instagram: {RED}erro — {ig_result.get('error', '?')}{RST}")
        print()

    # 3b — Vídeo Reel
    if fmt in ("video", "both"):
        video_result = _run_video(brand, topic, cta_text, dry_run)

        _log({
            "ts": started_at, "brand": brand_slug, "format": "video",
            "topic": topic, "output_dir": video_result.get("output_dir", ""),
            "dry_run": dry_run, "instagram": video_result.get("instagram", {}),
        })

        _h("CONCLUÍDO — VÍDEO")
        print(f"  MP4:      {video_result.get('video_path', '?')}")
        ig_v = video_result.get("instagram", {})
        if ig_v.get("ok"):
            print(f"  Instagram: {GREEN}https://instagram.com/p/{ig_v['code']}/{RST}")
        elif dry_run:
            print(f"  Instagram: {YELLOW}não postado (dry-run){RST}")
        else:
            print(f"  Instagram: {RED}erro — {video_result.get('error', ig_v.get('error', '?'))}{RST}")
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Designer AI — Agente Autônomo de Conteúdo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Autopiloto total — carrossel PNG (padrão)
  python agent.py --brand force-protocol

  # Reel MP4 com direção criativa do perfil
  python agent.py --brand force-protocol --format video

  # Carrossel + Vídeo na mesma rodada
  python agent.py --brand force-protocol --format both

  # Com tema específico
  python agent.py --brand force-protocol --topic "creatina e performance"

  # Gera tudo mas não posta (revisar antes)
  python agent.py --brand force-protocol --dry-run

  # Customizando carrossel
  python agent.py --brand force-protocol --slides 7 --type tese --cta "Comenta GUIA"

  # Ver marcas disponíveis
  python agent.py --list-brands
        """,
    )
    parser.add_argument("--brand",       metavar="SLUG",  help="Slug do perfil de marca")
    parser.add_argument("--format",      default="carousel", choices=["carousel", "video", "both"], help="Formato de saída: carousel (PNG), video (MP4 Reel), both (default: carousel)")
    parser.add_argument("--topic",       metavar="TEMA",  default="", help="Tema do conteúdo (opcional — agent pesquisa se omitido)")
    parser.add_argument("--slides",      type=int, default=9, choices=[5, 7, 9, 12], help="Número de slides — só para carrossel (default: 9)")
    parser.add_argument("--type",        default="", choices=["", "tendencia", "tese", "case", "previsao"], help="Tipo de carrossel (default: sugere pelo dia da semana)")
    parser.add_argument("--cta",         default="", help="Texto do CTA")
    parser.add_argument("--dry-run",     action="store_true", help="Gera conteúdo mas NÃO posta no Instagram")
    parser.add_argument("--post-only",   metavar="DIR",  help="Posta carrossel já gerado (pasta com PNGs + meta.json)")
    parser.add_argument("--list-brands", action="store_true", help="Lista perfis de marca disponíveis")
    args = parser.parse_args()

    # Posta carrossel já gerado sem regenerar
    if args.post_only:
        folder = Path(args.post_only)
        meta_file = folder / "meta.json"
        if not meta_file.exists():
            _err(f"meta.json não encontrado em {folder}")
            sys.exit(1)
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        slide_paths = sorted(str(folder / f) for f in os.listdir(folder) if f.endswith(".png") and not f.startswith("test"))
        slide_paths = [p for p in slide_paths if os.path.exists(p)]
        _h(f"POST-ONLY — {len(slide_paths)} PNGs de {folder.name}")
        for p in slide_paths:
            print(f"  → {Path(p).name}")
        ig = _post_instagram(
            slide_paths=slide_paths,
            caption=meta.get("caption", ""),
            hashtags=meta.get("hashtags", []),
        )
        if ig.get("ok"):
            _ok(f"Postado! https://instagram.com/p/{ig['code']}/")
        else:
            _err(f"Falha: {ig.get('error')}")
        return

    if args.list_brands:
        from designer.brand.profile import BrandProfile
        slugs = BrandProfile.list_saved()
        if not slugs:
            print("Nenhum perfil. Rode: python onboard.py")
        else:
            print("\nMarcas disponíveis:")
            for s in slugs:
                print(f"  → {s}")
        return

    if not args.brand:
        from designer.brand.profile import BrandProfile
        slugs = BrandProfile.list_saved()
        if not slugs:
            _err("Nenhum perfil encontrado. Rode: python onboard.py")
            sys.exit(1)
        print("\nMarcas disponíveis:")
        for i, s in enumerate(slugs, 1):
            print(f"  {i}. {s}")
        choice = input("\nEscolha (número ou slug): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(slugs):
            args.brand = slugs[int(choice) - 1]
        else:
            args.brand = choice

    # Sugere tipo de carrossel pelo dia da semana (editorial calendar)
    if not args.type:
        from generate_carousel import EDITORIAL_CALENDAR
        weekday = datetime.now().weekday()
        _, cal_type, cal_reason = EDITORIAL_CALENDAR.get(weekday, ("", "tendencia", ""))
        args.type = cal_type
        print(f"\n  {DIM}Calendário editorial:{RST} {BOLD}{args.type}{RST} ({cal_reason})")

    run(
        brand_slug=args.brand,
        topic=args.topic,
        n_slides=args.slides,
        carousel_type=args.type,
        cta_text=args.cta,
        dry_run=args.dry_run,
        fmt=args.format,
    )


if __name__ == "__main__":
    main()
