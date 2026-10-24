"""Cuánto tarda Qwen3-TTS en clonar una voz, por tamaño de modelo y dispositivo.

    python pruebas/medir_tts.py --voz mi_voz.m4a --modelos 0.6B,1.7B --devices cpu,mps

Imprime los segundos de cálculo por segundo de audio (x1.0 = tiempo real) y guarda cada prueba en salidas/pruebas/.
"""
import argparse
import sys
import time
from pathlib import Path

import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).parents[1]))
import reel  # noqa: E402

FRASE = ("En octubre se registraron doce mil novecientos ochenta y cuatro focos de calor, "
         "ciento veintiséis por ciento más que el promedio desde dos mil doce.")

p = argparse.ArgumentParser()
p.add_argument("--voz", required=True)
p.add_argument("--modelos", default="0.6B,1.7B")
p.add_argument("--devices", default="cpu")
a = p.parse_args()

salidas = reel.AQUI / "salidas" / "pruebas"
salidas.mkdir(parents=True, exist_ok=True)
audio = reel.cargar_audio(a.voz)
texto_ref = reel._transcribir(audio)
print(f"referencia: {len(audio) / 16000:.1f} s, «{texto_ref}»")

from qwen_tts import Qwen3TTSModel  # noqa: E402

for modelo in a.modelos.split(","):
    for device in a.devices.split(","):
        t = time.time()
        tts = Qwen3TTSModel.from_pretrained(f"Qwen/Qwen3-TTS-12Hz-{modelo}-Base", device_map=device, dtype=torch.float32)
        carga = time.time() - t
        prompt = tts.create_voice_clone_prompt(ref_audio=(audio, 16000), ref_text=texto_ref)
        t = time.time()
        wavs, sr = tts.generate_voice_clone(text=FRASE, language="Spanish", voice_clone_prompt=prompt)
        gen, dur = time.time() - t, len(wavs[0]) / sr
        sf.write(salidas / f"qwen_{modelo}_{device}.wav", wavs[0], sr)
        print(f"{modelo} {device}: carga {carga:.0f} s, genera {gen:.1f} s para {dur:.1f} s de audio (x{gen / dur:.2f})")
        del tts
