"""
Corrige TODOS os problemas do workflow Social Autopilot:
1. Adiciona header ngrok-skip-browser-warning em TODOS os nós HTTP
2. Remove referência ao nó Ads no Resultado Final (já removido)
3. Simplifica para content_type='carousel' (sem vídeo por enquanto)
4. Corrige o Consolidar para não falhar quando um branch não executa
"""
import json

with open("n8n/social_autopilot_workflow.json") as f:
    wf = json.load(f)

for node in wf["nodes"]:
    # 1. Adicionar header ngrok em TODOS os nós HTTP Request
    if node["type"] == "n8n-nodes-base.httpRequest":
        params = node["parameters"]
        if "headerParameters" in params:
            headers = params["headerParameters"]["parameters"]
            # Verifica se já tem o header
            has_ngrok = any(h.get("name") == "ngrok-skip-browser-warning" for h in headers)
            if not has_ngrok:
                headers.append({
                    "name": "ngrok-skip-browser-warning",
                    "value": "true"
                })
                print(f"  + ngrok header em: {node['name']}")

    # 2. Config: mudar content_type para 'carousel' (sem video por ora)
    if node["name"] == "\u2699\ufe0f Config do Cliente":
        old_js = node["parameters"]["jsCode"]
        node["parameters"]["jsCode"] = old_js.replace(
            "content_type: 'both'",
            "content_type: 'carousel'"
        )
        print("  + Config: content_type = 'carousel'")

    # 3. Resultado Final: remover referência ao nó Ads (já removido)
    if node["name"] == "\U0001f4ca Resultado Final":
        old_js = node["parameters"]["jsCode"]
        new_js = """const vars = $('Consolidar').item.json;
const copy = vars.copy;

// Monta URLs públicas das imagens (do Drive)
const image_urls = (vars.drive_urls || []).filter(u => u && !u.includes('mp4'));
const video_url = (vars.drive_urls || []).find(u => u && u.includes('mp4')) || null;

return {
  ok: true,
  brand: vars.brand_slug,
  brand_name: vars.brand_name,
  niche: vars.niche,
  topic: vars.topic,
  output_dir: vars.output_dir,
  headline: copy.headline_part1 + ' ' + copy.headline_part2,
  caption: copy.caption,
  hashtags: copy.hashtags,
  cover_path: vars.cover_path,
  video_path: vars.video_path,
  slide_paths: vars.slide_paths,
  drive_urls: vars.drive_urls,
  image_urls,
  video_url,
  auto_post: vars.auto_post,
  compliance_flags: vars.compliance_summary,
  generated_at: new Date().toISOString()
};"""
        node["parameters"]["jsCode"] = new_js
        print("  + Resultado Final: removida referência ao Ads")

    # 4. Consolidar: tornar robusto quando branch não executa
    if node["name"] == "Consolidar":
        new_js = """// Consolida resultados de carrossel e/ou vídeo
const vars = $('Montar payload').item.json;

let cover_path = null;
let video_path = null;
let slide_paths = [];
let drive_urls = [];

// Tenta ler carrossel (pode não ter executado)
try {
  const c = $('🖼️ Carrossel').item.json;
  if (c && c.ok) {
    cover_path = c.cover_path;
    slide_paths = c.slide_paths ?? [];
    drive_urls = drive_urls.concat(c.drive_urls ?? []);
  }
} catch(e) {
  // Carrossel não executou — OK
}

// Tenta ler vídeo (pode não ter executado)
try {
  const v = $('🎬 Vídeo').item.json;
  if (v && v.ok) {
    video_path = v.video_path;
    drive_urls = drive_urls.concat(v.drive_urls ?? []);
  }
} catch(e) {
  // Vídeo não executou — OK
}

return {
  ...vars,
  cover_path,
  video_path,
  slide_paths,
  drive_urls,
};"""
        node["parameters"]["jsCode"] = new_js
        print("  + Consolidar: robusto para branches não executados")

with open("n8n/social_autopilot_workflow.json", "w") as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("\nTodos os problemas corrigidos!")
