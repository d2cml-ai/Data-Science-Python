"""Compara narraciones con dos números: ritmo (palabras por segundo al hablar) y entonación (variación del tono).

    python pruebas/comparar_voces.py salidas_qwen salidas_voxcpm

Cada carpeta debe tener el reel.wav y el guion.json que dejó hacer_reel.py. Escuchar sigue siendo la prueba final:
más entonación no siempre suena mejor.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def prosodia(w, sr, palabras):
    """Palabras por segundo de habla (sin silencios) y desvío y rango p5-p95 del tono en semitonos."""
    w16 = librosa.resample(np.asarray(w, np.float32), orig_sr=sr, target_sr=16000)
    f0, sonoro, _ = librosa.pyin(w16, fmin=60, fmax=400, sr=16000)
    st = 12 * np.log2(f0[sonoro & ~np.isnan(f0)] / np.nanmedian(f0[sonoro]))
    habla = sum(fin - ini for ini, fin in librosa.effects.split(w16, top_db=35)) / 16000
    return {"duracion_s": len(w) / sr, "palabras_s": palabras / habla, "desvio_st": st.std(),
            "rango_st": np.percentile(st, 95) - np.percentile(st, 5), "sr": sr}


if __name__ == "__main__":
    for carpeta in map(Path, sys.argv[1:]):
        w, sr = sf.read(carpeta / "reel.wav")
        palabras = sum(len(e["frase"].split()) for e in json.loads((carpeta / "guion.json").read_text())["escenas"])
        m = prosodia(w, sr, palabras)
        print(f"{carpeta.name:16} {m['duracion_s']:5.1f} s | {m['palabras_s']:.2f} palabras/s | "
              f"entonación ±{m['desvio_st']:.2f} st, rango {m['rango_st']:.1f} st | {sr} Hz")
