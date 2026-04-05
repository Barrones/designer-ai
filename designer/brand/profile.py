"""BrandProfile — dados de marca de um cliente, persistidos em JSON."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _luminance(rgb: tuple[int, int, int]) -> float:
    """Percepção de brilho (0–255). Usa coeficientes ITU-R BT.601."""
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


@dataclass
class AudienceProfile:
    description: str
    age_range: str
    pains: list[str]
    desires: list[str]
    language: list[str]   # expressões que o público usa no dia a dia


@dataclass
class ColorPalette:
    primary: str          # fundo / cor dominante (hex)
    secondary: str        # elementos secundários (hex)
    accent: str           # destaque / CTA (hex)
    text: str = "#FFFFFF"


@dataclass
class Typography:
    headline: str = "Anton"
    body: str = "Inter"


@dataclass
class BrandProfile:
    # Identificadores
    slug: str              # ex: "suplementos-masculinos"
    client_name: str       # ex: "ForcaMax"

    # Nicho
    niche: str
    subniche: str
    product: str
    goal: str

    # Voz e estratégia
    tone: str
    content_pillars: list[str]
    content_angles: list[str]
    suggested_formats: list[str]

    # Público
    audience: AudienceProfile

    # Visual
    color_palette: ColorPalette
    typography: Typography

    # Inteligência de mercado
    market_gaps: list[str]
    competitor_patterns: list[str]

    # Meta
    handle: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Direção criativa por formato (opcional — enriquece output de vídeo e motion)
    creative_direction: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def save(self, profiles_dir: str = "brand_profiles") -> str:
        os.makedirs(profiles_dir, exist_ok=True)
        path = os.path.join(profiles_dir, f"{self.slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, slug: str, profiles_dir: str = "brand_profiles") -> "BrandProfile":
        path = os.path.join(profiles_dir, f"{slug}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def list_saved(cls, profiles_dir: str = "brand_profiles") -> list[str]:
        if not os.path.isdir(profiles_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(profiles_dir) if f.endswith(".json")]

    @classmethod
    def _from_dict(cls, d: dict) -> "BrandProfile":
        import dataclasses
        d = dict(d)
        d["audience"]      = AudienceProfile(**d["audience"])
        d["color_palette"] = ColorPalette(**d["color_palette"])
        d["typography"]    = Typography(**d["typography"])
        # Filtra campos desconhecidos para não quebrar com novos campos no JSON
        known = {f.name for f in dataclasses.fields(cls)}
        d = {k: v for k, v in d.items() if k in known}
        return cls(**d)

    # ------------------------------------------------------------------
    # Helpers para o renderer
    # ------------------------------------------------------------------

    def accent_rgb(self) -> tuple[int, int, int]:
        """
        Retorna a cor mais vívida da paleta para usar em texto de destaque.

        Percorre accent → secondary → primary e escolhe a primeira que seja
        suficientemente clara para ser legível sobre fundo escuro.
        Luminância mínima: 80/255 (~31%) — abaixo disso é muito escuro para texto.
        """
        candidates = [
            self.color_palette.accent,
            self.color_palette.secondary,
            self.color_palette.primary,
        ]
        for hex_color in candidates:
            rgb = _hex_to_rgb(hex_color)
            if _luminance(rgb) >= 80:
                return rgb
        # Fallback absoluto: vermelho coral sempre legível
        return (230, 57, 70)

    def designer_palette(self) -> dict:
        """
        Derive full Designer AI color palette from the brand's primary color.
        Uses config.derive_palette() with the most appropriate color.
        """
        from designer import config
        # Use accent as primary if it's vivid, otherwise use secondary
        primary_hex = self.color_palette.accent
        if primary_hex and primary_hex != "#FFFFFF":
            return config.derive_palette(primary_hex)
        if self.color_palette.secondary:
            return config.derive_palette(self.color_palette.secondary)
        return config.derive_palette(config.DEFAULT_BRAND_PRIMARY)
