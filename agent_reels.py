#!/usr/bin/env python3
"""
Designer AI — Agente de Reels
Pesquisa → Copy → Pexels (vídeo de fundo) → MP4 → Instagram

Usa a direção criativa do perfil da marca para escolher
o footage certo, o mood e o overlay visual.

Uso:
    python agent_reels.py --brand force-protocol
    python agent_reels.py --brand force-protocol --topic "creatina"
    python agent_reels.py --brand force-protocol --cta "Clica no link da bio"
    python agent_reels.py --brand force-protocol --dry-run
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import main as _main

if __name__ == "__main__":
    if "--format" not in sys.argv:
        sys.argv.insert(1, "video")
        sys.argv.insert(1, "--format")
    _main()
