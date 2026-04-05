#!/usr/bin/env python3
"""
Designer AI — Agente de Carrossel
Pesquisa → Headlines → Slides → PNG → Instagram

Uso:
    python agent_carousel.py --brand force-protocol
    python agent_carousel.py --brand force-protocol --topic "creatina"
    python agent_carousel.py --brand force-protocol --slides 7 --type tese
    python agent_carousel.py --brand force-protocol --dry-run
    python agent_carousel.py --brand force-protocol --post-only output/carousels/pasta/
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Delega para o agent.py principal com --format carousel
from agent import main as _main
import sys

if __name__ == "__main__":
    # Injeta --format carousel se não especificado
    if "--format" not in sys.argv:
        sys.argv.insert(1, "carousel")
        sys.argv.insert(1, "--format")
    _main()
