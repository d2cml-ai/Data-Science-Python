# Sesión 13 · De la voz al texto con modelos abiertos

Transcripción automática de entrevistas para antropología, sociología y psicología, solo con
modelos abiertos que corren en local: Whisper, Qwen3-ASR, Parakeet, Voxtral Realtime y MMS.

## Entorno

```bash
uv sync --group audio
uv run python sessions/13-audio-a-texto/datos.py   # audios de prueba (unos 30 MB)
uv run jupyter lab
```

Los modelos se descargan de Hugging Face la primera vez que se usan.

## Contenido

- `lecture/tutorial_corto_audio_a_texto.ipynb`: el tutorial de la clase. Cubre Whisper en
  CPU, Qwen3-ASR con contexto, alucinaciones, quechua de Huaylas con MMS y separación de hablantes.
- `slides/audio_a_texto.pdf`: los slides en Beamer (el fuente está en `audio_a_texto.tex`).
- `app/en_vivo.py`: transcripción en vivo desde el micrófono. Usa Voxtral Realtime si hay GPU
  y, si no, faster-whisper.
- `voz.py`: el mismo código para todos los modelos: cargar audio, VAD, transcribir, diarizar,
  exportar a CSV, SRT y TXT, y seudonimizar.
- `datos.py`: baja los audios, que tienen licencia libre. Son español peruano de OpenSLR 73,
  inglés de FLEURS y entrevistas de Wikimedia Commons.

## Datos

Los audios se guardan en `data/`, que no se versiona. Las fuentes y licencias de las
entrevistas están en `data/entrevistas/atribucion.csv`.
