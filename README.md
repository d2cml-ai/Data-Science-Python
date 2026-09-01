# Ciencia de Datos con Python — UP 2026-II

Material del curso. Una carpeta por tema del sílabo, en `sessions/`.

## Montar el entorno

```bash
uv sync --group geo      # solo lo que necesita la sesión de geoespacial
uv sync --all-groups     # todo el curso
uv run jupyter lab
```

Las versiones exactas están fijadas en `uv.lock`. No hace falta activar nada:
`uv run` se encarga.

## Sesiones

| # | Tema | Grupo de dependencias |
|---|------|----------------------|
| 01 | Ciencia de datos, Git y agentes de código | — |
| 02 | Fundamentos de Python | — |
| 03 | Web Scraping y APIs | `scraping` |
| 04 | MCPs en Claude Code | `llm` |
| 05 | Visualización y dashboards | `deploy` |
| 06 | Análisis geoespacial | `geo` |
| 07 | Datos raster | `raster` |
| 08 | LLMs, salidas estructuradas y RAG | `llm` |
| 09 | Hugging Face y fine-tuning | `hf` |
| 10 | Document AI y voz | `docai` |
| 11 | Agentes | `agents` |
| 12 | Despliegue y evaluación | `deploy` |

## Datos

No se versionan. Se descargan desde Hugging Face:

```bash
uv run python scripts/fetch_data.py 06-geoespacial
```

## Entregas

Van por GitHub Classroom, no por PR a este repo.
