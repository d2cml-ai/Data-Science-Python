# Tarea 1: clasificador de titulares de La República

**Pregunta:** ¿Pueden convertir titulares peruanos en un clasificador de noticias?

Autor: Roddy Huarhua · Medio: La República · Entrega: 18 de octubre de 2026

## Qué hay aquí

| Archivo | Para qué sirve |
|---|---|
| `01_recoleccion.ipynb` | Scraping de titulares y CSV con 7 columnas |
| `02_clasificacion.ipynb` | Etiquetado con LLM, zero-shot y fine-tuning |
| `app.py` | Dashboard en Streamlit |
| `data/` | CSV de titulares |
| `modelo/` | Modelo entrenado (sin los pesos, ver abajo) |

## Cómo correrlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

La clave de Anthropic va en un archivo `.env`: `ANTHROPIC_API_KEY=...`

## Datos

- Medio: La República
- Titulares recolectados: _por completar_
- Categorías: política, economía, deportes, ciencia/tecnología
- Descartados por no encajar: _por completar_

### Ética del scraping

- Se respetó `robots.txt`.
- User-Agent descriptivo con contacto.
- Pausa de 1 a 2 segundos entre pedidos y un solo reintento.
- _Documentar aquí si se usó RSS._

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
