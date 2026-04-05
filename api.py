"""
Designer AI — FastAPI Rendering Server
Expõe os endpoints de renderização para o n8n orquestrar.

Rodar:
    uv run uvicorn api:app --reload --port 8000

Endpoints:
    GET  /creators                 → lista criadores disponíveis
    POST /copy                     → gera copy via Claude
    POST /render/carousel          → renderiza carrossel PNG
    POST /render/video             → renderiza Reel MP4
    POST /render/ads               → gera pacote Google + Meta Ads
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Designer AI API", version="1.0.0")


@app.on_event("startup")
def _bootstrap():
    """No Railway: restaura o token OAuth a partir da variável de ambiente."""
    token_json = os.getenv("GOOGLE_OAUTH_TOKEN", "")
    if token_json:
        token_path = os.path.expanduser("~/.designer_ai_token.json")
        if not os.path.exists(token_path):
            with open(token_path, "w") as f:
                f.write(token_json)
            print("✅ OAuth token restaurado do env.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ──────────────────────────────────────────────────────────────────

class CopyRequest(BaseModel):
    brand_slug: str
    topic: str
    creator: Optional[str] = None


class CarouselRequest(BaseModel):
    brand_slug: str
    output_dir: str
    copy: dict


class VideoRequest(BaseModel):
    brand_slug: str
    output_dir: str
    copy: dict
    cta: str = "Saiba mais"
    duration: int = 15


class AdsRequest(BaseModel):
    brand_slug: str
    brand_name: str
    niche: str = ""
    output_dir: str
    copy: dict
    cover_image_path: str
    video_path: Optional[str] = None
    accent_color: str = "#00D4FF"


class Html5AdsRequest(BaseModel):
    headline1: str
    headline2: str
    cta: str = "Saiba mais"
    brand_name: str = "Brand"
    niche: str = ""
    accent_color: str = "#00D4FF"
    lang: str = "pt"
    sizes: Optional[list[str]] = None


class ResearchRequest(BaseModel):
    brand_slug: str
    niche: str = ""
    country: str = "BR"
    count: int = 5


class SocialPostRequest(BaseModel):
    brand_slug: str
    image_urls: list[str] = []
    video_url: Optional[str] = None
    caption: str = ""
    hashtags: list[str] = []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_output_dir(brand_slug: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("output", f"{brand_slug}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


def _upload_to_drive(files: list[str], brand_slug: str, topic: str, content_type: str) -> list[str]:
    """Faz upload para Drive se configurado. Retorna lista de URLs ou lista vazia."""
    if not os.getenv("GOOGLE_DRIVE_FOLDER_ID"):
        return []
    try:
        from designer.delivery.drive import upload_carousel
        return upload_carousel(files=files, brand_slug=brand_slug, topic=topic, content_type=content_type)
    except Exception as e:
        print(f"  ⚠ Drive upload: {e}")
        return []


def _dict_to_copy(d: dict):
    from designer.copy.headlines import CopyResult
    return CopyResult(
        formula=d.get("formula", "F1"),
        headline_part1=d.get("headline_part1", ""),
        headline_part2=d.get("headline_part2", ""),
        caption=d.get("caption", ""),
        hashtags=d.get("hashtags", []),
        image_query=d.get("image_query", ""),
        video_query=d.get("video_query", ""),
        compliance_flags=d.get("compliance_flags", []),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/creators")
def get_creators():
    try:
        from designer.research.creator_style import list_creators
        return {"creators": list_creators()}
    except Exception as e:
        return {"creators": [], "error": str(e)}


@app.post("/copy")
def generate_copy(req: CopyRequest):
    """Gera headline, legenda e hashtags via Claude."""
    try:
        from designer.brand.profile import BrandProfile
        from designer.copy.headlines import generate

        brand = BrandProfile.load(req.brand_slug)

        creator_style = None
        if req.creator:
            from designer.research.creator_style import extract_creator_style
            creator_style = extract_creator_style(req.creator)

        copy = generate(topic=req.topic, brand=brand, creator_style=creator_style)

        return {
            "ok": True,
            "formula": copy.formula,
            "headline_part1": copy.headline_part1,
            "headline_part2": copy.headline_part2,
            "caption": copy.caption,
            "hashtags": copy.hashtags,
            "image_query": copy.image_query,
            "video_query": copy.video_query,
            "compliance_flags": copy.compliance_flags,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/carousel")
def render_carousel(req: CarouselRequest):
    """Renderiza carrossel PNG e retorna caminhos dos arquivos."""
    try:
        from designer.brand.profile import BrandProfile
        from designer.image.unsplash import get_image_url
        from designer.visual.carousel import render_cover
        from designer.copy.slides import generate_slides
        from designer.visual.slide_renderer import render_slide

        brand = BrandProfile.load(req.brand_slug)
        copy = _dict_to_copy(req.copy)

        carousel_dir = os.path.join(req.output_dir, "carousel")
        os.makedirs(carousel_dir, exist_ok=True)

        handle = brand.handle or f"@{req.brand_slug}"
        accent_rgb = brand.accent_rgb()

        image_source = get_image_url(copy.image_query, topic=copy.headline_part1)

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

        slides = generate_slides(topic=copy.headline_part1, brand=brand, copy=copy)
        slide_paths = [cover_path]
        for slide in slides:
            sp = os.path.join(carousel_dir, f"0{slide.number + 1}_{slide.type}.png")
            render_slide(slide=slide, accent_color=accent_rgb, handle=handle, output_path=sp)
            slide_paths.append(sp)

        drive_urls = _upload_to_drive(slide_paths, req.brand_slug, "carousel", "carrosséis")

        return {
            "ok": True,
            "cover_path": cover_path,
            "slide_paths": slide_paths,
            "total_slides": len(slide_paths),
            "drive_urls": drive_urls,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/video")
def render_video(req: VideoRequest):
    """Renderiza Reel MP4 e retorna caminho do arquivo."""
    try:
        from designer.brand.profile import BrandProfile
        from designer.video.pexels_video import get_best_video
        from designer.video.composer import render_video as compose

        brand = BrandProfile.load(req.brand_slug)
        copy = _dict_to_copy(req.copy)

        video_bg = get_best_video(
            image_query=copy.video_query,
            topic=copy.headline_part1,
            orientation="portrait",
            min_duration=req.duration,
            max_duration=30,
        )

        output_video = os.path.join(req.output_dir, "reel.mp4")
        compose(
            video_path=video_bg,
            headline_part1=copy.headline_part1,
            headline_part2=copy.headline_part2,
            cta=req.cta,
            handle=brand.handle or f"@{req.brand_slug}",
            accent_color=brand.accent_rgb(),
            output_path=output_video,
            duration=req.duration,
        )

        drive_urls = _upload_to_drive([output_video], req.brand_slug, "reel", "videos")

        return {"ok": True, "video_path": output_video, "drive_urls": drive_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/render/ads")
def render_ads(req: AdsRequest):
    """Gera pacote de anúncios Google Ads + Meta Ads."""
    try:
        from designer.delivery.ads_export import export_ads_package

        copy = _dict_to_copy(req.copy)
        ads = export_ads_package(
            cover_image_path=req.cover_image_path,
            video_path=req.video_path,
            copy_result=copy,
            brand_name=req.brand_name,
            output_dir=req.output_dir,
            accent_color=req.accent_color,
            niche=req.niche,
        )

        ads_files = [ads.report_path]
        for f in Path(ads.google_ads_dir).glob("*"):
            ads_files.append(str(f))
        for f in Path(ads.meta_ads_dir).glob("*"):
            ads_files.append(str(f))
        drive_urls = _upload_to_drive(ads_files, req.brand_slug, req.brand_name + " — Ads", "ads")

        return {
            "ok": True,
            "google_ads_dir": ads.google_ads_dir,
            "meta_ads_dir": ads.meta_ads_dir,
            "report_path": ads.report_path,
            "google_copy": ads.google_copy,
            "meta_copy": ads.meta_copy,
            "drive_urls": drive_urls,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/html5")
def generate_html5(req: Html5AdsRequest):
    """Gera pacote de banners HTML5 standalone (sem precisar de carrossel/capa)."""
    try:
        from designer.delivery.html5_ads import generate_html5_pack, SIZES, DEFAULT_SIZES
        from designer.copy.headlines import CopyResult

        copy = CopyResult(
            formula="direct",
            headline_part1=req.headline1,
            headline_part2=req.headline2,
            caption="",
            hashtags=[],
            image_query="",
            video_query="",
            compliance_flags=[],
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"html5_{ts}")
        os.makedirs(output_dir, exist_ok=True)

        zips = generate_html5_pack(
            copy_result=copy,
            brand_name=req.brand_name,
            niche=req.niche,
            accent_color=req.accent_color,
            cta_text=req.cta,
            output_dir=output_dir,
            sizes=req.sizes,
            lang=req.lang,
        )

        return {
            "ok": True,
            "output_dir": output_dir,
            "zips": zips,
            "total": len(zips),
            "sizes_used": req.sizes or DEFAULT_SIZES,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/html5/sizes")
def list_html5_sizes():
    """Lista todos os formatos de banner HTML5 disponíveis."""
    from designer.delivery.html5_ads import SIZES, DEFAULT_SIZES
    return {
        "sizes": {k: {"width": v[0], "height": v[1]} for k, v in SIZES.items()},
        "defaults": DEFAULT_SIZES,
    }


# ── Research ──────────────────────────────────────────────────────────────────

@app.post("/research/topics")
def research_topics(req: ResearchRequest):
    """Pesquisa tendências do nicho e retorna temas para posts automaticamente."""
    try:
        from designer.research.brand_intel import research_brand
        from designer.brand.profile import BrandProfile

        niche = req.niche
        brand_name = req.brand_slug
        try:
            brand = BrandProfile.load(req.brand_slug)
            niche = niche or brand.subniche or brand.niche or ""
            brand_name = brand.client_name or req.brand_slug
        except Exception:
            pass

        if not niche:
            raise HTTPException(status_code=400, detail="Informe o nicho ou tenha um perfil salvo")

        intel = research_brand(
            brand_name=brand_name,
            niche=niche,
            country=req.country,
        )

        return {
            "ok": True,
            "topics": intel.topic_suggestions[:req.count],
            "trends": intel.trends,
            "pains": intel.pains,
            "angles": intel.angles,
            "tone": intel.tone,
            "total": len(intel.topic_suggestions),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Social Media Posting ──────────────────────────────────────────────────────

@app.post("/social/post")
def social_post(req: SocialPostRequest):
    """
    Posta conteúdo no Instagram via instagrapi (login com usuário/senha).

    Requer variáveis de ambiente:
      IG_USERNAME  — usuário do Instagram
      IG_PASSWORD  — senha do Instagram
    """
    from instagrapi import Client as IGClient
    from instagrapi.exceptions import LoginRequired
    import tempfile
    import urllib.request as _urllib

    username = os.getenv("IG_USERNAME", "")
    password = os.getenv("IG_PASSWORD", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="IG_USERNAME e IG_PASSWORD são obrigatórios")

    full_caption = req.caption
    if req.hashtags:
        full_caption += "\n\n" + " ".join(req.hashtags)

    # Login (reutiliza sessão se existir)
    session_path = Path(f"/tmp/ig_session_{username}.json")
    cl = IGClient()
    cl.delay_range = [1, 3]

    try:
        if session_path.exists():
            cl.load_settings(session_path)
            cl.login(username, password)
        else:
            cl.login(username, password)
        cl.dump_settings(session_path)
    except LoginRequired:
        cl.login(username, password)
        cl.dump_settings(session_path)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Falha no login do Instagram: {e}")

    try:
        # Baixa imagens/vídeo de URLs para arquivos temporários
        def _download(url: str, suffix: str) -> Path:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            _urllib.urlretrieve(url, tmp.name)
            return Path(tmp.name)

        if req.image_urls:
            if len(req.image_urls) == 1:
                # Post único
                img = _download(req.image_urls[0], ".jpg")
                media = cl.photo_upload(img, full_caption)
                img.unlink(missing_ok=True)
                return {"ok": True, "id": media.pk, "code": media.code, "type": "single"}
            else:
                # Carousel (álbum)
                imgs = [_download(url, ".jpg") for url in req.image_urls[:10]]
                media = cl.album_upload(imgs, full_caption)
                for p in imgs:
                    p.unlink(missing_ok=True)
                return {"ok": True, "id": media.pk, "code": media.code, "type": "carousel"}

        elif req.video_url:
            # Reel
            vid = _download(req.video_url, ".mp4")
            media = cl.clip_upload(vid, full_caption)
            vid.unlink(missing_ok=True)
            return {"ok": True, "id": media.pk, "code": media.code, "type": "reel"}
        else:
            raise HTTPException(status_code=400, detail="Envie image_urls ou video_url")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Autopilot ─────────────────────────────────────────────────────────────────

@app.post("/autopilot/trigger")
def autopilot_trigger(req: CopyRequest):
    """Endpoint para o n8n autopilot: gera copy + carrossel + vídeo + ads de uma vez."""
    try:
        from designer.brand.profile import BrandProfile

        brand = BrandProfile.load(req.brand_slug)

        # 1 — Gerar copy
        copy_resp = generate_copy(req)
        if not copy_resp.get("ok"):
            raise HTTPException(status_code=500, detail="Falha ao gerar copy")

        output_dir = _make_output_dir(req.brand_slug)

        # 2 — Carrossel
        carousel_resp = render_carousel(CarouselRequest(
            brand_slug=req.brand_slug,
            output_dir=output_dir,
            copy=copy_resp,
        ))

        # 3 — Vídeo
        video_resp = render_video(VideoRequest(
            brand_slug=req.brand_slug,
            output_dir=output_dir,
            copy=copy_resp,
        ))

        # 4 — Ads (se tem capa)
        ads_resp = None
        if carousel_resp.get("ok") and carousel_resp.get("cover_path"):
            ads_resp = render_ads(AdsRequest(
                brand_slug=req.brand_slug,
                brand_name=brand.client_name,
                niche=brand.subniche or "",
                output_dir=output_dir,
                copy=copy_resp,
                cover_image_path=carousel_resp["cover_path"],
                video_path=video_resp.get("video_path"),
            ))

        return {
            "ok": True,
            "output_dir": output_dir,
            "copy": copy_resp,
            "carousel": carousel_resp,
            "video": video_resp,
            "ads": ads_resp,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
