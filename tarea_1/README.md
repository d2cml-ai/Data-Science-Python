# Tarea 1: clasificador de titulares (La República y El Comercio)

**Pregunta:** ¿Pueden convertir titulares peruanos en un clasificador de noticias?

Autor: Roddy Huarhua · Opción C (comparada): 200 de La República + 200 de El Comercio · Entrega: 18 de octubre de 2026

## Qué hay aquí

| Archivo | Para qué sirve |
|---|---|
| `01_recoleccion.ipynb` | Lectura de feeds RSS, limpieza y CSV con 7 columnas |
| `02_clasificacion.ipynb` | Etiquetado con LLM, zero-shot y fine-tuning |
| `app.py` | Dashboard en Streamlit |
| `datos/` | `noticias.csv` y `etiquetas_llm.csv` |
| `modelo/` | Modelo entrenado (sin los pesos, ver abajo) |

## Cómo correrlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

La clave de Anthropic va en un archivo `.env`: `ANTHROPIC_API_KEY=...`

## Datos

- Medios: La República y El Comercio (opción C, meta 200 + 200)
- Fuente: feeds RSS oficiales, listados en el robots.txt de cada diario
- Se corre `01_recoleccion.ipynb` una vez al día y se acumula por URL, porque cada feed cubre solo unos 2 días
- Titulares recolectados: _por completar_
- Categorías: política, economía, deportes, ciencia/tecnología
- Descartados por no encajar (sociedad, espectáculos, mundo, etc.): ver sección 5 del notebook 01
- `seccion_original` es el primer tramo de la URL; `etiqueta` sale del mapeo explícito de esa sección a las 4 categorías

### Ética del scraping

- Se respetó `robots.txt` de ambos diarios (se consulta con `RobotFileParser` en el notebook).
- Se usó RSS en lugar de scrapear HTML: La República prohíbe la paginación y ofrece `/rss/` como canal público.
- User-Agent descriptivo con contacto.
- Pausa de 1 a 2 segundos entre pedidos y un solo reintento.

## Resultados (conjunto de prueba)

| Métrica | Valor |
|---|---|
| F1 macro, modelo ajustado | _por completar_ |
| F1 macro, zero-shot | _por completar_ |
| Acuerdo LLM-humano | _por completar_ / 20 |

## Modelo

Los pesos pesan más de 100 MB y no se suben a GitHub. Para regenerarlos, correr
`02_clasificacion.ipynb` completo.

## Dashboard

_Link o captura de la ejecución local._
