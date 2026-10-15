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
- Titulares recolectados: **562** en dos corridas (13 y 14 de octubre): La República 249, El Comercio 313
- Utilizables para el clasificador (sin `otra`): **546**, con La República 242 y El Comercio 304, ambos sobre la meta de 200
- La República rota despacio en el RSS; para llegar a la meta se siguieron enlaces entre notas (sin paginación, con tope y pausa). Eso trajo notas atemporales (guías de trámites, AFP, plazo fijo) con fechas de 2021 a 2026: 40 de las 249 son anteriores a julio de 2026
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
| F1 macro, BETO ajustado | **0.921** (accuracy 0.93) |
| F1 macro, zero-shot (BETO-XNLI) | 0.700 (accuracy 0.72) |
| Acuerdo LLM-humano | 34 / 40 (85 %) en dos muestras de 20 |

Conjunto de prueba: 110 titulares (20 %, estratificado, `random_state=42`); entrenamiento: 436.
Por clase (F1): deportes 0.97, política 0.93, ciencia/tecnología 0.91, economía 0.88.

### Cómo leer estos números

- La "verdad" de entrenamiento y prueba es la etiqueta del LLM (Claude Haiku 5.5), no una etiqueta humana. El F1 mide cuánto reproduce el modelo al LLM; frente a un humano el techo es el 85 % de acuerdo.
- En 7 de 20 notas de la segunda muestra el humano marcó `otra` (guías y servicios) y el LLM solo en 1. Es un criterio más estricto que el del LLM, y se decidió no aplicarlo al entrenamiento (ver `BITACORA.md`, D11).
- Un solo split y una sola semilla, con 110 notas de prueba: el F1 tiene un margen de varios puntos. Tómese como "alrededor de 0.9".
- Economía es la clase más débil: se confunde con política, sobre todo en notas de pensiones, AFP y feriados.
- Con el dataset de 390 notas el F1 fue 0.920 y el zero-shot 0.609; el ajuste fino mejora al zero-shot en 0.2 a 0.3 puntos de F1 en ambas corridas.

## Modelo

Los pesos pesan más de 100 MB y no se suben a GitHub. Para regenerarlos, correr
`02_clasificacion.ipynb` completo.

## Dashboard

Se corre en local con `streamlit run app.py` (requiere el modelo en `modelo/`). Verificado el 14 de octubre:
el servidor levanta y el modelo clasifica correctamente titulares de prueba de las cuatro categorías.
