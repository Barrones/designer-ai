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
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Designer AI API", version="1.0.0")

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_output_dir(brand_slug: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("output", f"{brand_slug}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


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

        return {
            "ok": True,
            "cover_path": cover_path,
            "slide_paths": slide_paths,
            "total_slides": len(slide_paths),
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

        return {"ok": True, "video_path": output_video}
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

        return {
            "ok": True,
            "google_ads_dir": ads.google_ads_dir,
            "meta_ads_dir": ads.meta_ads_dir,
            "report_path": ads.report_path,
            "google_copy": ads.google_copy,
            "meta_copy": ads.meta_copy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
