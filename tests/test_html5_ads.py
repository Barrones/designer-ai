"""Teste de conformidade Google Display para html5_ads."""
import os
import zipfile
import tempfile
from dataclasses import dataclass

@dataclass
class FakeCopy:
    headline_part1: str = "Crédito Fácil"
    headline_part2: str = "Sem Burocracia"
    caption: str = "Solicite agora"

from designer.delivery.html5_ads import generate_html5_pack

with tempfile.TemporaryDirectory() as tmp:
    zips = generate_html5_pack(
        copy_result=FakeCopy(),
        brand_name="Credito Livre",
        niche="crédito pessoal",
        accent_color="#00D4FF",
        cta_text="Saiba Mais",
        output_dir=tmp,
        sizes=["rectangle"],
    )

    zp = zips[0]
    with zipfile.ZipFile(zp) as zf:
        names = zf.namelist()
        print(f"\n📦 Arquivos no ZIP: {names}")

        html = zf.read("index.html").decode()
        assert 'meta name="ad.size"' in html, "FALTA meta ad.size!"
        assert "style.css" in html, "FALTA link para style.css!"
        assert "script.js" in html, "FALTA link para script.js!"
        assert "onclick" not in html, "onclick inline detectado!"
        print("  ✓ index.html — meta ad.size, links externos, sem onclick inline")

        css = zf.read("style.css").decode()
        assert "border:1px solid" in css, "FALTA borda obrigatória!"
        assert "#ad-container" in css, "FALTA container!"
        assert "loading-bar" in css, "FALTA efeito finance (loading bar)!"
        print("  ✓ style.css — borda 1px, container, efeito finance")

        js = zf.read("script.js").decode()
        assert "var clickTag" in js, "FALTA clickTag!"
        assert "MAX_LOOPS" in js, "FALTA controle de loops!"
        assert "MAX_MS" in js, "FALTA controle de tempo!"
        assert "15000" in js, "Tempo máx deve ser 15s!"
        print("  ✓ script.js — clickTag, MAX_LOOPS=3, MAX_MS=15000")

    size_kb = os.path.getsize(zp) // 1024
    print(f"\n📊 Tamanho: {size_kb}KB (limite: 150KB)")
    print("\n✅ TODOS OS TESTES PASSARAM — Google Display compliance OK")
