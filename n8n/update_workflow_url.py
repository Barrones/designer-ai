"""
Gerencia workflows do Designer AI no n8n.

Comandos:
    uv run python n8n/update_workflow_url.py update <URL>     — Atualiza URL da API no workflow existente
    uv run python n8n/update_workflow_url.py push              — Envia/atualiza todos os workflows no n8n
    uv run python n8n/update_workflow_url.py push-autopilot    — Envia só o autopilot original
    uv run python n8n/update_workflow_url.py push-social       — Envia o Social Media Autopilot (autônomo)
    uv run python n8n/update_workflow_url.py list               — Lista workflows no n8n

Exemplo:
    uv run python n8n/update_workflow_url.py push
    uv run python n8n/update_workflow_url.py update https://designer-ai.railway.app
"""
import json
import os
import sys
import urllib.request
import urllib.error

N8N_URL  = "https://n8n.fluxonocodebarrao.com.br"
N8N_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYjJhYzUxOS0zMzE2LTRjNTAtYWU5OC1iZGQ3MjM4NGQxZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOTFmODNkYmEtZDgwYS00ZTcyLWE3MmItMTcyOWMwMDlmN2U0IiwiaWF0IjoxNzc1Mjc4ODAwfQ.0Kzdfyi1hsRDILSzA4APqZLCFm0QqQ88_jnqOBKg7yE"

# IDs dos workflows no n8n
PIPELINE_WF_ID = "4Gl87pSUIb4msekz"  # Content Pipeline (original)
AUTOPILOT_WF_ID = "oWTgqyG6otakdAGD"  # Autopilot (criado em 2026-04-04)
SOCIAL_WF_ID = "yJosQLvynqks7gTo"  # Social Media Autopilot

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _request(method, path, body=None):
    url = N8N_URL + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode() if e.fp else ""
        print(f"❌ HTTP {e.code}: {body_err[:300]}")
        raise


def _load_local_workflow(filename):
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path) as f:
        return json.load(f)


def cmd_list():
    """Lista todos os workflows no n8n."""
    data = _request("GET", "/api/v1/workflows")
    workflows = data.get("data", data) if isinstance(data, dict) else data
    print(f"\n📋 Workflows em {N8N_URL}:\n")
    for wf in workflows:
        active = "🟢" if wf.get("active") else "⚪"
        print(f"  {active} {wf['id']}  {wf['name']}")
    print()


def cmd_update(new_url):
    """Atualiza a URL da API FastAPI no workflow existente."""
    old_url = "http://localhost:8000"
    new_base = new_url.rstrip("/")

    for wf_id, label in [(PIPELINE_WF_ID, "Pipeline"), (AUTOPILOT_WF_ID, "Autopilot")]:
        if not wf_id:
            print(f"⏭️  {label}: sem ID configurado, pulando.")
            continue

        print(f"\n🔄 [{label}] Buscando workflow {wf_id}...")
        wf = _request("GET", f"/api/v1/workflows/{wf_id}")
        wf_str = json.dumps(wf)
        count = wf_str.count(old_url)

        if count == 0:
            print(f"  ℹ️  Nenhuma URL localhost encontrada.")
            continue

        updated = json.loads(wf_str.replace(old_url, new_base))
        payload = {
            "name": updated["name"],
            "nodes": updated["nodes"],
            "connections": updated["connections"],
            "settings": updated.get("settings", {}),
            "active": updated.get("active", False),
        }
        result = _request("PUT", f"/api/v1/workflows/{wf_id}", payload)
        print(f"  ✅ {count} URL(s) atualizadas! {old_url} → {new_base}")
        print(f"     {N8N_URL}/workflow/{result['id']}")


def cmd_push(only_autopilot=False, only_social=False):
    """Envia workflows locais para o n8n."""
    workflows_to_push = []

    if only_social:
        workflows_to_push.append((
            "social_autopilot_workflow.json",
            SOCIAL_WF_ID,
            "Social Media Autopilot",
        ))
    elif only_autopilot:
        workflows_to_push.append((
            "autopilot_workflow.json",
            AUTOPILOT_WF_ID,
            "Autopilot",
        ))
    else:
        workflows_to_push.append((
            "designer_ai_workflow.json",
            PIPELINE_WF_ID,
            "Content Pipeline",
        ))
        workflows_to_push.append((
            "autopilot_workflow.json",
            AUTOPILOT_WF_ID,
            "Autopilot",
        ))
        workflows_to_push.append((
            "social_autopilot_workflow.json",
            SOCIAL_WF_ID,
            "Social Media Autopilot",
        ))

    for filename, wf_id, label in workflows_to_push:
        print(f"\n📦 [{label}] Carregando {filename}...")
        wf = _load_local_workflow(filename)

        payload = {
            "name": wf["name"],
            "nodes": wf["nodes"],
            "connections": wf["connections"],
            "settings": wf.get("settings", {}),
        }

        if wf_id:
            # Atualizar workflow existente
            print(f"  ✏️  Atualizando workflow {wf_id}...")
            result = _request("PUT", f"/api/v1/workflows/{wf_id}", payload)
            print(f"  ✅ Atualizado! {N8N_URL}/workflow/{result['id']}")
        else:
            # Criar novo workflow
            print(f"  🆕 Criando novo workflow...")
            result = _request("POST", "/api/v1/workflows", payload)
            new_id = result["id"]
            print(f"  ✅ Criado! ID: {new_id}")
            print(f"     {N8N_URL}/workflow/{new_id}")
            print(f"\n  ⚠️  IMPORTANTE: Atualize AUTOPILOT_WF_ID = \"{new_id}\" neste script!")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()
    elif cmd == "update":
        if len(sys.argv) < 3:
            print("Uso: ... update https://SUA-URL.railway.app")
            sys.exit(1)
        cmd_update(sys.argv[2])
    elif cmd == "push":
        cmd_push(only_autopilot=False)
    elif cmd == "push-autopilot":
        cmd_push(only_autopilot=True)
    elif cmd == "push-social":
        cmd_push(only_social=True)
    else:
        print(f"Comando desconhecido: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
