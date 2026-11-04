"""Copia las skills y los agentes de este repositorio a tu carpeta personal de Claude Code.

    python instalar.py                 # copia a ~/.claude/skills y ~/.claude/agents
    python instalar.py --desinstalar   # borra solo lo que este proyecto instaló

Después de instalar, reinicia Claude Code (terminal, app de escritorio o VS Code) y escribe /skills.
Solo toca las carpetas y archivos con los nombres de este proyecto; no borra otras skills.
"""

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ["buy-vs-rent", "peru-listings-search", "peru-safe-investments", "rent-vs-buy-model", "streamlit-dashboard"]
AGENTS = ["market-data", "opportunity-cost", "financial-analysis", "streamlit-builder"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--destino", default=str(Path.home() / ".claude"), help="carpeta de Claude Code (por defecto ~/.claude)")
    p.add_argument("--desinstalar", action="store_true")
    a = p.parse_args()
    dest = Path(a.destino)
    (dest / "skills").mkdir(parents=True, exist_ok=True)
    (dest / "agents").mkdir(parents=True, exist_ok=True)

    for name in SKILLS:
        target = dest / "skills" / name
        if target.exists():
            shutil.rmtree(target)
        if not a.desinstalar:
            shutil.copytree(HERE / ".claude" / "skills" / name, target,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(("borrada " if a.desinstalar else "skill   ") + str(target))
    for name in AGENTS:
        target = dest / "agents" / f"{name}.md"
        if a.desinstalar:
            target.unlink(missing_ok=True)
        else:
            shutil.copy2(HERE / ".claude" / "agents" / f"{name}.md", target)
        print(("borrado " if a.desinstalar else "agente  ") + str(target))
    if not a.desinstalar:
        print("\nListo. Reinicia Claude Code y llama al orquestador con /buy-vs-rent")


if __name__ == "__main__":
    main()
