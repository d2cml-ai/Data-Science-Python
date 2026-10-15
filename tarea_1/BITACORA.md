# Bitácora de decisiones · Tarea 1

Registro de qué decidimos, por qué y con qué evidencia. Cada decisión apunta al
issue y al commit donde quedó implementada, para que se pueda reconstruir el
trabajo en orden.

Enunciado: [d2cml-ai/Data-Science-Python#188](https://github.com/d2cml-ai/Data-Science-Python/issues/188).
Issues propios: #1 (recolección), #2 (etiquetado con LLM), #3 (clasificador y dashboard).

## Resumen

| # | Fecha | Decisión | Motivo | Issue |
|---|---|---|---|---|
| D1 | 13 oct | Leer RSS y no scrapear HTML | robots.txt de La República prohíbe paginación y ofrece `/rss/` como canal público; el enunciado acepta RSS | #1 |
| D2 | 13 oct | Pasar de la opción A a la **opción C** (200 + 200) | Con RSS solo, La República daba 83 titulares útiles; el enunciado permite la opción comparada | #1 |
| D3 | 13 oct | Sección = primer tramo de la URL; mapeo explícito a las 4 categorías | El Comercio no trae `<category>` en su feed; así los dos medios usan el mismo criterio | #1 |
| D4 | 13 oct | Descartar y reportar lo que no encaja (sociedad, espectáculos, mundo…) | El enunciado prohíbe una quinta categoría | #1 |
| D5 | 13 oct | Acumular por URL en una corrida diaria | Cada feed cubre unos 2 días; una sola descarga no alcanza la meta | #1 |
| D6 | 13 oct | Etiquetar con Claude Haiku 5.5, lista cerrada y sin tildes | Modelo pequeño y barato; la respuesta se normaliza porque a veces llega `Política` | #2 |
| D7 | 13 oct | Muestra humana de 20 **sin** etiqueta del LLM ni de la sección | Evitar que el juicio humano quede influido | #2 |
| D8 | 13 oct | Entorno de trabajo fuera de OneDrive | OneDrive sincroniza miles de archivos de un entorno virtual y rompe enlaces físicos | #2 |
| D9 | 13 oct | Seguir enlaces entre notas de La República (con tope por sección) | Tras la 2.ª corrida seguía en 85 de 200; el RSS no iba a alcanzar | #3 |
| D10 | 13 oct | Revocar la clave de API **después** de entregar | Quedó visible en la sesión de trabajo; riesgo bajo y la clave vence el 12 nov | — |

## Detalle

### D1 · RSS en lugar de HTML

**Evidencia:** `robots.txt` de La República prohíbe `/*/pag/`, `/*/tag/`, `/archivo/*` y
el buscador, y marca como públicos `/rss/` y `/sitemap/`. El Comercio lista sus
feeds por categoría como sitemaps. El enunciado dice que un bloqueo resuelto con RSS
no baja puntaje, pero un scraping agresivo sí.

**Alternativas descartadas:** paginar las secciones (prohibido por robots.txt);
scrapear HTML de toda la web (más pedidos, sin ganancia frente al RSS).

### D2 · Opción C

**Evidencia (primera corrida, 13 oct):**

| Medio | Titulares en las 4 categorías |
|---|---|
| La República | 83 |
| El Comercio | 157 |

La opción A (solo La República, 350 a 400) quedaba a más del 75 % de distancia.
La opción C pide 200 + 200 y El Comercio ya estaba cerca.

**Riesgo asumido:** La República sigue siendo el límite (ver D9).

### D3 y D4 · Sección y descartes

`seccion_original` es el primer tramo de la URL (`/politica/2026/...`). El mapeo es
explícito en el notebook 01:

| seccion_original | etiqueta |
|---|---|
| politica | politica |
| economia | economia |
| deportes, deporte-total | deportes |
| ciencia, tecnologia | ciencia_tecnologia |

En la primera corrida se descartaron 155 de 452 notas (sociedad 60, espectáculos 20,
mundo 15, etc.). El reporte está en la sección 5 del notebook 01.

**Limitación conocida:** la etiqueta por sección no es la verdad absoluta: una nota
de la sección Política puede tratar de economía. Por eso el LLM etiqueta aparte
(D6) y se miden los desacuerdos.

### D5 · Corridas diarias

Cada corrida de `01_recoleccion.ipynb` agrega las notas nuevas y elimina repetidas por
URL. Evidencia de avance:

| Corrida | La República | El Comercio | Total |
|---|---|---|---|
| 1 (13 oct) | 83 | 157 | 240 |
| 2 (13 oct, horas después) | 85 | 189 | 274 |

La segunda corrida mostró que La República apenas rota: +2 notas útiles en unas horas.

### D6 · Etiquetado con LLM

- Modelo: `claude-haiku-5-5`, con la instrucción de responder una sola palabra de una lista cerrada.
- Las etiquetas se guardan en `datos/etiquetas_llm.csv` y no se vuelven a pedir.
- Hallazgos de implementación: esta API ya no acepta `temperature`; la respuesta puede
  traer un bloque de razonamiento antes del texto, así que se busca el bloque `text`.

**Resultado (240 titulares):** coincidencia con la sección 93.75 %. Validación humana
sobre 20: **acuerdo 20/20**. Con 20 casos y una sola nota `otra`, este número no
prueba que el LLM sea perfecto; se reporta con esa salvedad.

### D8 · Entorno fuera de OneDrive

El entorno virtual vive en `C:\Users\huarh\venvs\tarea1`. En la carpeta sincronizada
`uv` falló al crear enlaces físicos y habría subido miles de archivos a la nube.

### D9 · Seguir enlaces entre notas de La República

**Problema:** 85 de 200 tras dos corridas; los feeds rotan despacio.

**Alternativas evaluadas:**

| Opción | Resultado |
|---|---|
| Más corridas de RSS | Insuficiente: unas decenas más en toda la semana |
| Cambiar a opción A o B | Peor: 350 a 400 de un solo medio |
| Entregar con lo que haya | Pierde puntos de recolección; es el plan de respaldo |
| **Seguir enlaces entre notas** | Elegida |

**Reglas para no ser agresivos:**

- solo notas de las 4 secciones, nunca paginación, tags ni archivo;
- consulta a `robots.txt` por cada URL;
- pausa de 1.5 s y un solo reintento;
- tope de 60 notas por sección, para no desbalancear;
- máximo de 250 pedidos por corrida;
- User-Agent descriptivo con contacto.

**Resultado:** La República llegó a 200 y El Comercio a 199 (399 en total). Ver sección 8 del notebook 01.

### D10 · Clave de API

Un paso de verificación imprimió la clave en el resultado de una herramienta. Se
decidió **no rotarla de inmediato** (queda solo en la máquina local y en la sesión,
y vence el 12 de noviembre). El 14 de octubre se decidió además **no revocarla**:
solo la conoce el equipo. La clave nunca se escribe en
un notebook y `.env` está en `.gitignore`.

### D11 · Segunda validación humana y etiqueta para entrenar

**Evidencia:** 20 notas nuevas al azar (`datos/muestra_revision_2.csv`), mostradas sin
la etiqueta del LLM ni la de la sección.

| Comparación | Acuerdo |
|---|---|
| Humano vs. LLM | 14 / 20 |
| Humano vs. sección | 12 / 20 |
| LLM vs. sección | 16 / 20 |

Sumando la primera muestra, humano vs. LLM es **34 / 40 = 85 %**.

**Hallazgo:** en 7 de 20 notas el humano marcó `otra` (guías de trámites, hípica,
una nota judicial); el LLM lo hizo en 1. El criterio humano es más estricto.

**Decisión:** entrenar con la etiqueta del **LLM** y descartar las 9 notas `otra`
(390 notas). No se aplica el criterio estricto del humano al entrenamiento, para no
vaciar el dataset ni desbalancear ciencia/tecnología. Queda como limitación en el README.

### D12 · Corrida del 14 de octubre y re-entrenamiento

**Resultado:** 562 titulares (La República 249, El Comercio 313); 546 utilizables.
Re-entrenado con 436 / 110: F1 macro **0.921** (BETO ajustado) frente a **0.700** (zero-shot).

**Limitación:** el seguimiento de enlaces (D9) trajo notas atemporales de La República
con fechas de 2021 a 2026 (40 de 249 anteriores a julio de 2026). Se mantienen porque el
enunciado no fija rango de fechas, y se reportan como limitación.

## Pendiente

- [x] Etiquetar con el LLM las notas nuevas de La República (399 de 399; coincidencia con la sección 90.23 %, 9 `otra`)
- [x] Decidir qué hacer con las 9 notas `otra` y con el ruido de la etiqueta por sección en economía (D11)
- [x] Zero-shot, fine-tuning y evaluación en prueba (issue #3): F1 macro 0.609 vs 0.920 sobre 78 notas (13 oct)
- [x] Seguir acumulando notas por RSS en más de un día, hasta superar 200 + 200 **utilizables** (sin `otra`), y volver a entrenar (D12)
- [x] `app.py` funcionando y README con métricas
- [x] ~~Revocar la clave de API tras la entrega~~: el usuario decidió no revocarla (14 oct); la clave solo la tiene el equipo (D10)
