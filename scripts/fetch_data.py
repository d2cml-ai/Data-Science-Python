"""Descarga los datasets del curso desde Hugging Face.

Uso:
    python scripts/fetch_data.py               # todo
    python scripts/fetch_data.py 06-geoespacial   # solo una sesion
"""
import sys
from pathlib import Path

REPO_ID = "aquiro1994/ds-python-up"
ROOT = Path(__file__).resolve().parent.parent


def main(subset: str | None = None) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        sys.exit("Falta huggingface_hub:  uv add huggingface-hub")

    patterns = [f"{subset}/**"] if subset else None
    path = snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=ROOT / "data",
        allow_patterns=patterns,
    )
    print(f"Datos en: {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
