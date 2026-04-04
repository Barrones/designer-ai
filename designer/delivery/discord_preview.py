"""
Discord Preview — envia o conteúdo gerado para aprovação no Discord.

Fluxo:
  1. Envia imagem/vídeo + legenda no canal
  2. Adiciona reações ✅ ❌
  3. Aguarda resposta (timeout configurável)
  4. Retorna True (aprovado) ou False (rejeitado/timeout)

Requer no .env (compartilhado com o projeto Agente):
  DISCORD_BOT_TOKEN=...
  DISCORD_CHANNEL_ID=...
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Tenta carregar .env do Designer e do Agente
load_dotenv()
_agente_env = os.path.join(
    os.path.expanduser("~"), "Library", "Mobile Documents",
    "com~apple~CloudDocs", "Cursor",
    "Agente de IA para criação de conteúdo", ".env",
)
if os.path.exists(_agente_env):
    load_dotenv(_agente_env, override=False)

APPROVE = "✅"
REJECT  = "❌"


def send_for_approval(
    file_path: str,
    brand_slug: str,
    topic: str,
    caption: str = "",
    timeout_seconds: int = 300,
) -> bool:
    """
    Envia o arquivo para o canal Discord e aguarda aprovação.

    Parameters
    ----------
    file_path       : caminho local do arquivo (PNG ou MP4)
    brand_slug      : slug da marca
    topic           : tema do conteúdo
    caption         : legenda / copy do post
    timeout_seconds : tempo máximo de espera (padrão: 5 min)

    Returns
    -------
    True se aprovado (✅), False se rejeitado (❌) ou timeout.
    """
    return asyncio.run(_run_preview(file_path, brand_slug, topic, caption, timeout_seconds))


async def _run_preview(
    file_path: str,
    brand_slug: str,
    topic: str,
    caption: str,
    timeout_seconds: int,
) -> bool:
    import discord

    token      = os.getenv("DISCORD_BOT_TOKEN", "")
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

    if not token or not channel_id:
        print("  ⚠ Discord não configurado — pulando preview")
        return True  # aprovação automática se não configurado

    approved = False
    intents  = discord.Intents.default()
    intents.reactions = True
    intents.message_content = True

    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        nonlocal approved

        channel = bot.get_channel(channel_id)
        if not channel:
            await bot.close()
            return

        # Monta a mensagem de preview
        file_type = "Vídeo" if file_path.endswith(".mp4") else "Carrossel"
        header = (
            f"**{file_type} para aprovação**\n"
            f"Marca: `{brand_slug}` | Tema: _{topic}_\n"
            f"Reaja com {APPROVE} para aprovar ou {REJECT} para rejeitar.\n"
        )

        if caption:
            # Trunca legenda longa
            short_cap = caption[:800] + "..." if len(caption) > 800 else caption
            header += f"\n**Legenda:**\n{short_cap}"

        # Envia arquivo
        discord_file = discord.File(file_path, filename=Path(file_path).name)
        msg = await channel.send(content=header, file=discord_file)

        await msg.add_reaction(APPROVE)
        await msg.add_reaction(REJECT)

        print(f"\n  Discord: aguardando aprovação ({timeout_seconds}s)...")
        print(f"  Canal: #{channel.name} — reaja com {APPROVE} ou {REJECT}\n")

        def check(reaction, user):
            return (
                reaction.message.id == msg.id
                and not user.bot
                and str(reaction.emoji) in (APPROVE, REJECT)
            )

        try:
            reaction, _ = await asyncio.wait_for(
                bot.wait_for("reaction_add", check=check),
                timeout=timeout_seconds,
            )
            approved = str(reaction.emoji) == APPROVE
            status   = "APROVADO ✅" if approved else "REJEITADO ❌"
            await channel.send(f"Conteúdo **{status}**")
        except asyncio.TimeoutError:
            await channel.send(f"⏱ Timeout — conteúdo **não aprovado** (sem resposta em {timeout_seconds}s)")
            approved = False

        await bot.close()

    await bot.start(token)
    return approved
