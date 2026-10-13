# Sesión 10 · Document AI y voz

## Entorno

```bash
uv sync --group docai
uv run jupyter lab
```

## Contenido

- `assets`
- `lab`
- `lab-vision-models.ipynb`
- `lab-voz`
- `lecture`
  - `paddleocr_documentos_peruanos.ipynb` — clase de OCR con PaddleOCR 3.7 sobre documentos
    peruanos (impresos, fotos y manuscritos), con aceleración por GPU en Mac (MPS)

## Datos

Los datasets viven en Hugging Face, no en este repo:

```bash
uv run python scripts/fetch_data.py 10-document-ai-voz
```

La clase de PaddleOCR es la excepción: baja sus imágenes de Wikimedia Commons (unos 15 MB) a
`lecture/data/paddleocr/` la primera vez que se ejecuta. Los modelos (unos 2,2 GB) también se
descargan solos en esa primera corrida.
