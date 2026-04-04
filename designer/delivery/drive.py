"""
Google Drive Delivery — faz upload dos arquivos gerados para uma pasta do Drive.

Requer no .env:
  GOOGLE_DRIVE_FOLDER_ID=id_da_pasta_destino
  GOOGLE_OAUTH_CREDENTIALS=oauth_client_secret.json  (Desktop App OAuth2)

Na primeira execução abre o browser para autenticar.
Token salvo em ~/.designer_ai_token.json para reutilização.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_TOKEN_PATH = os.path.expanduser("~/.designer_ai_token.json")
_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None

    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
        return creds

    if creds and creds.valid:
        return creds

    # Resolve caminho do client secret
    oauth_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "oauth_client_secret.json")
    candidates = [
        oauth_path,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", oauth_path),
        os.path.join(
            os.path.expanduser("~"), "Library", "Mobile Documents",
            "com~apple~CloudDocs", "Cursor", "Designer ", oauth_path,
        ),
    ]

    client_secret_path = None
    for c in candidates:
        c = os.path.normpath(c)
        if os.path.exists(c):
            client_secret_path = c
            break

    if not client_secret_path:
        raise EnvironmentError(
            "Arquivo oauth_client_secret.json não encontrado.\n"
            "Crie em: console.cloud.google.com → Credenciais → + Criar → ID do cliente OAuth 2.0 → App para computador"
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, _SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def _save_token(creds) -> None:
    with open(_TOKEN_PATH, "w") as f:
        f.write(creds.to_json())


def upload_carousel(
    files: list[str],
    brand_slug: str,
    topic: str,
    content_type: str = "carrosséis",   # "carrosséis" ou "videos"
    subfolder: bool = True,
) -> list[str]:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    if not folder_id:
        raise EnvironmentError("Configure GOOGLE_DRIVE_FOLDER_ID no .env")

    credentials = _get_credentials()
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    # Estrutura: raiz → Carrosseis ou Videos → marca — tema
    target_folder_id = folder_id
    if subfolder:
        type_folder_id  = _get_or_create_folder(service, content_type, folder_id)
        folder_name     = f"{brand_slug} — {topic[:40]}"
        target_folder_id = _get_or_create_folder(service, folder_name, type_folder_id)

    urls = []
    for file_path in files:
        if not os.path.exists(file_path):
            continue

        file_name = Path(file_path).name
        if file_path.endswith(".mp4"):
            mime_type = "video/mp4"
        elif file_path.endswith(".png"):
            mime_type = "image/png"
        else:
            mime_type = "application/json"

        media     = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file_meta = {"name": file_name, "parents": [target_folder_id]}

        uploaded = service.files().create(
            body=file_meta,
            media_body=media,
            fields="id,webViewLink",
        ).execute()

        file_id  = uploaded.get("id", "")
        view_url = uploaded.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()

        urls.append(view_url)
        print(f"  ✓ Drive: {file_name}")

    return urls


def _get_or_create_folder(service, name: str, parent_id: str) -> str:
    query = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files   = results.get("files", [])

    if files:
        return files[0]["id"]

    folder_meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=folder_meta, fields="id").execute()
    return folder["id"]
