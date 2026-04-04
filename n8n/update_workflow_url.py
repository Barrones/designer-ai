"""
Atualiza a URL do FastAPI no workflow do n8n.

Uso (depois de fazer deploy no Railway):
    uv run python n8n/update_workflow_url.py https://designer-ai.railway.app
"""
import json
import sys
import urllib.request
import urllib.error

N8N_URL  = "https://n8n.fluxonocodebarrao.com.br"
N8N_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYjJhYzUxOS0zMzE2LTRjNTAtYWU5OC1iZGQ3MjM4NGQxZjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOTFmODNkYmEtZDgwYS00ZTcyLWE3MmItMTcyOWMwMDlmN2U0IiwiaWF0IjoxNzc1Mjc4ODAwfQ.0Kzdfyi1hsRDILSzA4APqZLCFm0QqQ88_jnqOBKg7yE"
WORKFLOW_ID = "4Gl87pSUIb4msekz"
OLD_URL  = "http://localhost:8000"


def _request(method, path, body=None):
    url = N8N_URL + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    if len(sys.argv) < 2:
        print("Uso: uv run python n8n/update_workflow_url.py https://SUA-URL.railway.app")
        sys.exit(1)

    new_base = sys.argv[1].rstrip("/")
    print(f"🔄 Buscando workflow {WORKFLOW_ID}...")

    wf = _request("GET", f"/api/v1/workflows/{WORKFLOW_ID}")

    # Substitui todas as ocorrências da URL antiga pela nova
    wf_str = json.dumps(wf)
    updated_str = wf_str.replace(OLD_URL, new_base)
    wf_updated = json.loads(updated_str)

    count = wf_str.count(OLD_URL)
    if count == 0:
        print("ℹ️  Nenhuma URL localhost encontrada — workflow já pode estar atualizado.")
        return

    print(f"✏️  Atualizando {count} URL(s): {OLD_URL} → {new_base}")

    payload = {
        "name": wf_updated["name"],
        "nodes": wf_updated["nodes"],
        "connections": wf_updated["connections"],
        "settings": wf_updated.get("settings", {}),
        "active": wf_updated.get("active", False),
    }

    result = _request("PUT", f"/api/v1/workflows/{WORKFLOW_ID}", payload)
    print(f"✅ Workflow atualizado! ID: {result['id']}")
    print(f"   Acesse: {N8N_URL}/workflow/{WORKFLOW_ID}")


if __name__ == "__main__":
    main()
