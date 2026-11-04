"""Open the Streamlit dashboard for this example.

    python run_dashboard.py

Works from any shell (PowerShell, cmd, bash) and from any folder. It uses the launcher in the repository
(../Skill_Buy_Rent) and falls back to the installed skill in ~/.claude/skills. Stop the server with Ctrl+C.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAUNCHERS = [
    HERE.parent / "Skill_Buy_Rent" / ".claude" / "skills" / "buy-vs-rent" / "scripts" / "hl.py",
    Path.home() / ".claude" / "skills" / "buy-vs-rent" / "scripts" / "hl.py",
]


def main() -> int:
    launcher = next((p for p in LAUNCHERS if p.exists()), None)
    if launcher is None:
        print("Launcher not found. Install the skills with: python ../Skill_Buy_Rent/install.py")
        return 1
    runs = sorted((p for p in (HERE / "outputs").iterdir() if (p / "inputs.json").exists()), reverse=True)
    if not runs:
        print("No run folder found in outputs/.")
        return 1
    print(f"Opening the dashboard for {runs[0].name} at http://localhost:8501 (Ctrl+C to stop)")
    return subprocess.call([sys.executable, str(launcher), "dashboard", "--run", str(runs[0])], cwd=HERE)


if __name__ == "__main__":
    raise SystemExit(main())
