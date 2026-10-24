"""¿El estilo entre paréntesis de VoxCPM2 cambia la narración? La misma frase sin estilo, con estilo en inglés y en español.

    python pruebas/estilos_voxcpm.py --voz mi_voz.m4a --device mps
"""
import argparse
import sys
import time
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).parents[1]))
import reel  # noqa: E402
from comparar_voces import prosodia  # noqa: E402

FRASE = ("Octubre es el más intenso desde dos mil doce, con doce mil novecientos ochenta y cuatro "
         "focos detectados por satélite.")
ESTILOS = {"sin_estilo": "",
           "locutor_en": "(confident news anchor, energetic, slightly faster pace)",
           "locutor_es": "(locutor de noticiero, enérgico y seguro, ritmo un poco más rápido)"}

p = argparse.ArgumentParser()
p.add_argument("--voz", required=True)
p.add_argument("--device", default="cpu")
a = p.parse_args()

salidas = reel.AQUI / "salidas" / "pruebas"
salidas.mkdir(parents=True, exist_ok=True)
voz = reel.VozExpresiva(a.voz, device=a.device)
palabras = len(FRASE.split())
for nombre, estilo in ESTILOS.items():
    t = time.time()
    w = voz.tts.generate(text=estilo + FRASE, reference_wav_path=str(voz.ref), cfg_value=2.0, inference_timesteps=10)
    gen, dur = time.time() - t, len(w) / voz.sr
    sf.write(salidas / f"voxcpm_{nombre}.wav", w, voz.sr)
    m = prosodia(w, voz.sr, palabras)
    print(f"{nombre:11} genera {gen:4.1f} s para {dur:4.1f} s (x{gen / dur:.2f}) | {m['palabras_s']:.2f} palabras/s | "
          f"entonación ±{m['desvio_st']:.2f} st | WER {reel._wer(FRASE, reel._a16k(w, voz.sr)):.2f}")
