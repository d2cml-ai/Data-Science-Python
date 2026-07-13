# Presentación QLAB-PUCP · IA y Data Science en Acción

Presentación informativa (≈30 min) del curso **Ciencia de Datos e IA para Ciencias Sociales**.

> **Título:** Inteligencia Artificial y Data Science en Acción: herramientas prácticas para el análisis de datos.

## Cómo presentar

Es una presentación HTML autocontenida (reveal.js desde CDN — necesita internet la primera vez).

```bash
# Opción 1 — abrir directamente
open Presentacion_QLAB_2026/index.html

# Opción 2 — servidor local (recomendado, evita bloqueos del navegador)
cd Presentacion_QLAB_2026
python -m http.server 8000
# luego abre http://localhost:8000
```

## Controles

| Tecla | Acción |
|---|---|
| `→` / `Espacio` | Siguiente |
| `←` | Anterior |
| `F` | Pantalla completa |
| `S` | Vista del presentador (speaker notes) |
| `O` | Vista general (overview) de todas las diapositivas |
| `Esc` | Salir de overview |

## Estructura (≈23 diapositivas)

1. Portada
2–5. El curso, a quién va dirigido y los dos bloques (fundamentos + IA)
6–9. **Parte 2 — Agent Coding** (Claude Code, Codex, caso BCRP con MCP)
10–14. **Tema 1 · Análisis geoespacial** (GeoPandas, Folium, raster)
15–18. **Tema 2 · OCR con PaddleOCR** — incluye **escáner animado** del caso `cyo-licitaciones`
19–21. **Tema 3 · Whishper** — incluye **waveform de audio animado** + transcripción
22–23. Cierre

> Las secciones de OCR y Whisper usan **animaciones CSS propias** (línea de escaneo de
> documento y visualizador de audio) para reforzar visualmente el mensaje.

## Imágenes

Están en `assets/`, copiadas de los labs reales del curso (mapas de COVID, hospitales,
brecha digital de Cusco y dashboard de precipitación).

## Para exportar a PDF

Abre la presentación con `?print-pdf` al final de la URL y usa "Imprimir → Guardar como PDF":

```
http://localhost:8000/?print-pdf
```
