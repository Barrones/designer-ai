"""Valida geração em 3 idiomas com efeitos de nicho."""
import zipfile
import tempfile
from dataclasses import dataclass
from designer.delivery.html5_ads import generate_html5_pack

@dataclass
class Copy:
    headline_part1: str = ""
    headline_part2: str = ""
    caption: str = ""

TESTS = [
    {"lang": "pt", "niche": "finance",   "expect_html": "Analisando seu perfil", "expect_lang": "pt-BR"},
    {"lang": "en", "niche": "ecommerce", "expect_html": "Special offer for you", "expect_lang": "en"},
    {"lang": "es", "niche": "premium",   "expect_html": "La exclusividad que mereces", "expect_lang": "es"},
    {"lang": "en", "niche": "tech",      "expect_html": "Smart solution",        "expect_lang": "en"},
    {"lang": "pt", "niche": "default",   "expect_html": "clientes atendidos",    "expect_lang": "pt-BR"},
]

for t in TESTS:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Copy(headline_part1="Test H1", headline_part2="Test H2")
        zips = generate_html5_pack(
            copy_result=copy, brand_name="Test", niche=t["niche"],
            accent_color="#00D4FF", cta_text="CTA", output_dir=tmp,
            sizes=["rectangle"], lang=t["lang"],
        )
        with zipfile.ZipFile(zips[0]) as zf:
            html = zf.read("index.html").decode()
            assert f'lang="{t["expect_lang"]}"' in html, f'FALTA lang={t["expect_lang"]} para {t["lang"]}'
            assert t["expect_html"] in html, f'Texto "{t["expect_html"]}" não encontrado para lang={t["lang"]} niche={t["niche"]}'
        print(f'  ✓ {t["lang"]} + {t["niche"]:<10} → "{t["expect_html"]}"')

print("\n✅ Todos os idiomas e nichos OK")
