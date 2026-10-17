"""Transcripción en vivo desde el micrófono, en la terminal. Ctrl+C para terminar.

    uv run python sessions/13-audio-a-texto/app/en_vivo.py                      # Voxtral si hay GPU; si no, Whisper
    uv run python sessions/13-audio-a-texto/app/en_vivo.py --motor whisper --idioma es
    uv run python sessions/13-audio-a-texto/app/en_vivo.py --archivo entrevista.ogg   # simula el micrófono
"""
import argparse
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voz  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--motor", choices=["auto", "voxtral", "whisper"], default="auto")
p.add_argument("--idioma", default="es")
p.add_argument("--archivo", help="audio para simular el micrófono")
a = p.parse_args()
motor = a.motor if a.motor != "auto" else ("voxtral" if voz.dispositivo() != "cpu" else "whisper")
print(f"Cargando {motor}...", flush=True)
if motor == "voxtral":
    vivo = voz.VoxtralEnVivo(voz.Transcriptor("voxtral-realtime"))
    vivo.empezar()
else:
    vivo = voz.CasiEnVivo(voz.Transcriptor("faster-whisper"), idioma=a.idioma)

cola = queue.Queue()
BLOQUE = voz.SR // 10  # 100 ms
if a.archivo:
    x = voz.cargar_audio(a.archivo)

    def alimentar():
        for i in range(0, len(x), BLOQUE):
            cola.put(x[i:i + BLOQUE])
            time.sleep(0.1)
        cola.put(None)
    threading.Thread(target=alimentar, daemon=True).start()
    flujo = None
else:
    import sounddevice as sd
    flujo = sd.InputStream(samplerate=voz.SR, channels=1, dtype="float32", blocksize=BLOQUE,
                           callback=lambda d, *_: cola.put(d[:, 0].copy()))
    flujo.start()
print("Escuchando... (Ctrl+C para terminar)\n", flush=True)

n = 0
try:
    while (trozo := cola.get()) is not None:
        if motor == "voxtral":
            vivo.agregar(trozo)
            for *_, texto in vivo.eventos[n:]:
                print(texto, end="", flush=True)
            n = len(vivo.eventos)
        elif frase := vivo.agregar(trozo):
            print(frase, flush=True)
except KeyboardInterrupt:
    pass
if flujo:
    flujo.stop()
final = vivo.terminar()
if motor == "voxtral":
    for *_, texto in vivo.eventos[n:]:
        print(texto, end="", flush=True)
salida = Path(__file__).resolve().parents[1] / "data" / "salidas" / f"en_vivo_{time.strftime('%Y%m%d_%H%M%S')}.txt"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(final, encoding="utf-8")
print(f"\n\nGuardado en {salida}")
