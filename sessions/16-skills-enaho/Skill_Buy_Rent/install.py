"""Copy this repository's skills and agents to your personal Claude Code folder.

    python install.py               # copies to ~/.claude/skills and ~/.claude/agents
    python install.py --uninstall   # removes only what this project installed

After installing, restart Claude Code (terminal, desktop app or VS Code) and type /skills.
Only folders and files with this project's names are touched; other skills are left alone.
"""

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ["buy-vs-rent", "peru-listings-search", "peru-safe-investments", "rent-vs-buy-model", "streamlit-dashboard"]
AGENTS = ["market-data", "opportunity-cost", "financial-analysis", "streamlit-builder"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target", default=str(Path.home() / ".claude"), help="Claude Code folder (default ~/.claude)")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args()
    dest = Path(a.target)
    (dest / "skills").mkdir(parents=True, exist_ok=True)
    (dest / "agents").mkdir(parents=True, exist_ok=True)

    for name in SKILLS:
        target = dest / "skills" / name
        if target.exists():
            shutil.rmtree(target)
        if not a.uninstall:
            shutil.copytree(HERE / ".claude" / "skills" / name, target,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(("removed " if a.uninstall else "skill   ") + str(target))
    for name in AGENTS:
        target = dest / "agents" / f"{name}.md"
        if a.uninstall:
            target.unlink(missing_ok=True)
        else:
            shutil.copy2(HERE / ".claude" / "agents" / f"{name}.md", target)
        print(("removed " if a.uninstall else "agent   ") + str(target))
    if not a.uninstall:
        print("\nDone. Restart Claude Code and call the orchestrator with /buy-vs-rent")


if __name__ == "__main__":
    main()
