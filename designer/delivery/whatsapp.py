"""
WhatsApp Approval — Z-API (sem Docker, sem Meta approval)

Fluxo:
  1. Envia mensagem + preview para o número configurado
  2. Aguarda resposta "SIM" ou "NÃO" (polling por timeout)
  3. Retorna True (aprovado) ou False (rejeitado/timeout)

Requer no .env:
  ZAPI_INSTANCE_ID=...
  ZAPI_TOKEN=...
  ZAPI_PHONE=5511999999999   # número com DDI, sem + ou espaços
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

_BASE = "https://api.z-api.io/instances/{instance}/token/{token}"

APPROVE_WORDS = {"sim", "s", "yes", "ok", "aprova", "aprovado", "✅", "👍"}
REJECT_WORDS  = {"nao", "não", "n", "no", "rejeita", "rejeitado", "❌", "👎"}


def _url(path: str) -> str:
    instance = os.getenv("ZAPI_INSTANCE_ID", "")
    token    = os.getenv("ZAPI_TOKEN", "")
    if not instance or not token:
        raise RuntimeError("ZAPI_INSTANCE_ID e ZAPI_TOKEN são obrigatórios no .env")
    return f"{_BASE.format(instance=instance, token=token)}/{path}"


def _phone() -> str:
    phone = os.getenv("ZAPI_PHONE", "")
    if not phone:
        raise RuntimeError("ZAPI_PHONE é obrigatório no .env (ex: 5511999999999)")
    return phone.strip().lstrip("+").replace(" ", "").replace("-", "")


def send_text(message: str) -> bool:
    """Envia mensagem de texto via Z-API."""
    try:
        resp = requests.post(
            _url("send-text"),
            json={"phone": _phone(), "message": message},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"  ⚠ WhatsApp send-text falhou: {e}")
        return False


def send_image(file_path: str, caption: str = "") -> bool:
    """Envia imagem com legenda via Z-API (upload base64)."""
    import base64

    try:
        data = Path(file_path).read_bytes()
        b64  = base64.b64encode(data).decode()
        ext  = Path(file_path).suffix.lstrip(".").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        resp = requests.post(
            _url("send-image"),
            json={
                "phone":   _phone(),
                "image":   f"data:{mime};base64,{b64}",
                "caption": caption,
            },
            timeout=30,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"  ⚠ WhatsApp send-image falhou: {e}")
        return False


def _get_last_message(after_timestamp: float) -> str | None:
    """
    Busca última mensagem recebida após `after_timestamp`.
    Retorna o texto em lowercase ou None se não houver nada novo.
    """
    try:
        resp = requests.get(
            _url("chats"),
            params={"phone": _phone()},
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        chats = resp.json()
        if not isinstance(chats, list) or not chats:
            return None

        last = chats[0]
        # Z-API retorna timestamp em ms
        msg_ts = last.get("lastMessageTime", 0) / 1000
        if msg_ts <= after_timestamp:
            return None

        text = last.get("lastMessage", {}).get("text", {}).get("message", "")
        return text.lower().strip() if text else None
    except Exception:
        return None


def send_for_approval(
    file_path: str,
    brand_slug: str,
    topic: str,
    caption: str = "",
    timeout_seconds: int = 300,
) -> bool:
    """
    Envia prévia para WhatsApp e aguarda aprovação.

    Parameters
    ----------
    file_path       : caminho local do arquivo (PNG/JPG/MP4)
    brand_slug      : slug da marca
    topic           : tema do conteúdo
    caption         : copy do post (opcional, truncado em 300 chars)
    timeout_seconds : tempo máximo de espera (padrão: 5 min)

    Returns
    -------
    True se aprovado, False se rejeitado ou timeout.
    """
    # Verifica configuração
    instance = os.getenv("ZAPI_INSTANCE_ID", "")
    token    = os.getenv("ZAPI_TOKEN", "")
    phone    = os.getenv("ZAPI_PHONE", "")

    if not instance or not token or not phone:
        print("  ⚠ WhatsApp não configurado — pulando aprovação")
        return True  # aprovação automática

    file_type = "Vídeo" if str(file_path).endswith(".mp4") else "Carrossel"
    short_cap = caption[:300] + "..." if len(caption) > 300 else caption

    # Mensagem de contexto
    msg = (
        f"🎨 *{file_type} pronto para aprovação*\n"
        f"Marca: *{brand_slug}* | Tema: _{topic}_\n\n"
        f"Responda *SIM* para aprovar ou *NÃO* para rejeitar.\n"
        f"_(aguardando {timeout_seconds}s)_"
    )
    if short_cap:
        msg += f"\n\n*Legenda:*\n{short_cap}"

    # Envia preview (imagem ou texto se MP4)
    ext = Path(str(file_path)).suffix.lower()
    sent = False

    if ext in (".png", ".jpg", ".jpeg"):
        sent = send_image(str(file_path), caption=msg)
    else:
        # Para MP4/outros: envia só texto com aviso
        sent = send_text(msg + f"\n\n📎 Arquivo: {Path(str(file_path)).name}")

    if not sent:
        print("  ⚠ Falha ao enviar WhatsApp — aprovação automática")
        return True

    print(f"  WhatsApp: aguardando aprovação ({timeout_seconds}s)...")
    print(f"  Número: {phone[:4]}****{phone[-4:]} — responda SIM ou NÃO\n")

    # Polling — verifica resposta a cada 5s
    start_ts = time.time()
    poll_interval = 5

    while (time.time() - start_ts) < timeout_seconds:
        time.sleep(poll_interval)
        reply = _get_last_message(after_timestamp=start_ts)

        if reply is None:
            continue

        if any(w in reply for w in APPROVE_WORDS):
            send_text("✅ Conteúdo *APROVADO* — postando agora!")
            print("  WhatsApp: APROVADO ✅")
            return True

        if any(w in reply for w in REJECT_WORDS):
            send_text("❌ Conteúdo *REJEITADO* — descartando.")
            print("  WhatsApp: REJEITADO ❌")
            return False

    # Timeout
    send_text(f"⏱ Timeout — conteúdo *não aprovado* (sem resposta em {timeout_seconds}s)")
    print(f"  WhatsApp: timeout após {timeout_seconds}s")
    return False
