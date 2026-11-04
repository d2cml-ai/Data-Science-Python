# Skill_Buy_Rent · ¿Comprar o alquilar en Lima? Skills de Claude Code

Cinco skills y cuatro subagentes de Claude Code que responden **«¿me conviene comprar o alquilar?»** para una búsqueda
concreta en Lima. Una skill orquestadora hace las preguntas, dos agentes investigan en paralelo (avisos reales de venta
y alquiler; qué rendiría la cuota inicial si se invierte), un tercero corre el modelo financiero y un cuarto revisa el
dashboard y exporta las figuras.

El usuario da un rango de precio, área mínima y dormitorios, distritos, el porcentaje de cuota inicial y lo que quiera
agregar. La herramienta compara comprar con hipoteca contra alquilar una vivienda parecida e invertir el dinero que no
se usa en la compra (el costo de oportunidad), por distrito, a 5, 10, 15, 20 y 30 años y con varias tasas hipotecarias.

> Uso educativo. No es asesoría financiera, tributaria ni de inversión personalizada.

## Cómo llamar al orquestador

La skill orquestadora es **`buy-vs-rent`**. Se llama de tres formas, en cualquier Claude Code: la terminal, la app de
escritorio (pestaña Code) o la extensión de VS Code.

| Forma | Qué escribir | Qué pasa |
|---|---|---|
| Comando | `/buy-vs-rent` | Hace las cinco preguntas y corre todo |
| Pedido normal | «¿Me conviene comprar o alquilar un depa en Surco?» | La skill se activa sola por su `description` |
| Prueba sin internet | `/buy-vs-rent fixture` | Corre todo con datos **sintéticos** de prueba |

Las preguntas son: rango de precio en soles, área mínima y dormitorios, distritos (de uno a seis), porcentaje de cuota
inicial y extras (estacionamiento, estreno, mascotas, cuota máxima, antigüedad). Al final responde con el veredicto por
distrito y horizonte, y deja todo en `salidas/` y `figuras/` de la carpeta donde se trabaja.

## Instalar

Las skills viven en dos lugares, con el mismo contenido:

| Dónde | Para qué |
|---|---|
| `.claude/skills/` y `.claude/agents/` de este repositorio | Versionadas con git; se activan al abrir Claude Code en esta carpeta |
| `~/.claude/skills/` y `~/.claude/agents/` de tu laptop | Disponibles en **cualquier** carpeta y proyecto, también desde la app de escritorio |

```bash
cd sessions/16-skills-enaho/Skill_Buy_Rent
python instalar.py               # copia las 5 skills y los 4 agentes a ~/.claude
```

Reinicien Claude Code y escriban `/skills`: deben aparecer las cinco. Si cambian algo en el repositorio, vuelvan a
correr `python instalar.py`. Para quitarlas: `python instalar.py --desinstalar`.

Requisitos: Python 3.11 o más (probado con 3.14) con pandas, numpy, streamlit, plotly, matplotlib, jsonschema y pyyaml.
`pyproject.toml` los declara; con `uv` o `pip`:

```bash
uv sync              # o: pip install -e ".[test]"
```

No hace falta instalar el paquete: el motor (`housing_lima`) va dentro de la skill orquestadora y su lanzador lo
encuentra solo.

## Lo esencial

- **Una skill es una carpeta** con `SKILL.md` (bloque YAML con `name` y `description`, y las instrucciones),
  `reference.md` con el detalle que se carga solo si hace falta, y `scripts/` con lo que no se discute.
- **El orquestador no hace el trabajo pesado.** Pregunta, valida, lanza los agentes y resume. Los agentes se pasan
  archivos en una carpeta de corrida, no mensajes, así el contexto de cada uno queda limpio.
- **Un solo modelo.** Las fórmulas están una sola vez, en `housing_lima`. El análisis, las figuras y el dashboard
  usan el mismo código.
- **Nada inventado.** Cada aviso y cada número investigado lleva su URL y su fecha. Lo que no tiene fuente queda como
  `null`, se reemplaza por un supuesto con nombre y se muestra como advertencia («necesita tu dato»).
- **Todo se valida.** Cada archivo que pasa de un agente a otro se valida contra un esquema JSON antes del paso
  siguiente. Si falla, se detiene.

### Las skills y los agentes

| Skill | La usa | Entra | Sale |
|---|---|---|---|
| `buy-vs-rent` | Tú (orquestador) | Las cinco respuestas | `salidas/<corrida>/inputs.json` y el resumen final |
| `peru-listings-search` | agente `market-data` | `inputs.json` | `listings.csv`, `market_summary.json`, `housing_params.json` |
| `peru-safe-investments` | agente `opportunity-cost` | `inputs.json` | `opportunity_costs.json` (depósito a plazo, S&P 500, BVL) |
| `rent-vs-buy-model` | agente `financial-analysis` | Los cuatro archivos anteriores | `analysis_results.csv`, `analysis_summary.json`, `analysis_report.md` |
| `streamlit-dashboard` | agente `streamlit-builder` | La corrida completa | `figuras/*.png` y el dashboard probado |

```text
/buy-vs-rent ── preguntas ── salidas/<corrida>/inputs.json
      ├──► market-data        (avisos reales)        ┐ en paralelo
      ├──► opportunity-cost   (costo de oportunidad) ┘
      ▼
   financial-analysis  ──►  streamlit-builder  ──►  salidas/validacion.txt, figuras/, dashboard
```

## Las salidas

| Carpeta | Qué hay | ¿En git? |
|---|---|---|
| `salidas/<corrida>/` | Todos los archivos de una corrida: avisos, parámetros, resultados, `analysis_report.md`, `validacion.txt` | No (se regeneran) |
| `salidas/validacion.txt` | Resumen de la última validación: avisos por distrito, datos sin fuente, veredictos | Sí |
| `figuras/` | `veredictos.png`, `<distrito>_patrimonio.png`, `<distrito>_mapa_calor_20a.png` (200 dpi) | Sí |
| `datos/listings.csv` | Avisos que tú pegas a mano si los portales bloquean la búsqueda (plantilla en la skill `peru-listings-search`) | No |

Las figuras y la validación que vienen en el repositorio salen de la corrida de prueba con **datos sintéticos**.

## El dashboard

```bash
python .claude/skills/buy-vs-rent/scripts/hl.py dashboard --run salidas/<corrida>
```

(Si instalaron las skills, el lanzador también está en `~/.claude/skills/buy-vs-rent/scripts/hl.py`.) Funciona sin
internet. En la barra lateral se mueven la tasa hipotecaria, la cuota inicial, el costo de oportunidad (las tres
opciones o una tasa propia, en escenario bajo, base o alto), el precio (dentro de tu rango; por defecto la mediana de
los avisos encontrados), el descuento por negociación, el plazo, el crecimiento de precios y alquileres, y términos
reales o nominales. Muestra el veredicto por distrito, un mapa de calor, el patrimonio en el tiempo, los avisos con sus
enlaces, los supuestos con sus fuentes y botones de descarga.

## Comandos del motor

Todos con `python .claude/skills/buy-vs-rent/scripts/hl.py <comando>` desde la carpeta de trabajo:

| Comando | Qué hace |
|---|---|
| `check-env` | Revisa Python y paquetes |
| `new-run --answers a.json` | Valida las respuestas y crea `salidas/<corrida>/inputs.json` |
| `listings --run D --raw f.csv --source-mode live\|csv\|mixed` | Normaliza, deduplica, marca atípicos y calcula precio y alquiler realistas |
| `validate --run D --stage research\|analysis\|all` | Valida contra los esquemas y escribe `validacion.txt` |
| `analyze --run D` | Corre el modelo |
| `summary --run D` | Resumen corto para el orquestador |
| `figures --run D` | Exporta las figuras a `figuras/` |
| `check-app --run D` | Prueba el dashboard con AppTest |
| `dashboard --run D` | Abre el dashboard |
| `fixture-run` | Corrida completa con datos sintéticos |

## Validación

Corrida de prueba (`/buy-vs-rent fixture`), con datos **sintéticos**: S/ 250–400 mil, 60 m², 2 dormitorios, 20 % de
cuota inicial, Jesús María, Pueblo Libre y San Miguel.

| Chequeo | Resultado |
|---|---|
| Cuota de S/ 100,000 al 8 % TEA en 20 años | S/ 819 y saldo cero tras 240 cuotas |
| Avisos sin URL descartados | 3 de 138 |
| Duplicados entre portales / atípicos | 3 / 3, marcados y conservados |
| Avisos en dólares convertidos a soles | 3, con el tipo de cambio registrado |
| Precio realista Jesús María / Pueblo Libre / San Miguel | S/ 362,000 / 349,875 / 338,000 |
| Datos sin fuente mostrados como advertencia | 5 (crecimiento del alquiler, seguros, impuestos de las 3 opciones) |
| Pruebas automáticas | 94 de 94 pasan (`python -m pytest -q`) |

El detalle está en [`salidas/validacion.txt`](salidas/validacion.txt).

## Evaluar

En [`evaluacion.md`](evaluacion.md) están los pedidos para correr con y sin skills y lo que debería salir.

```bash
claude -p "/buy-vs-rent fixture"                                                 # con skills
claude -p --disallowedTools Skill "¿Me conviene comprar o alquilar en Lima?"     # sin skills
```

## Entrega

```text
.claude/skills/
  buy-vs-rent/            SKILL.md, reference.md, scripts/hl.py, scripts/housing_lima/ (motor, esquemas, app)
  peru-listings-search/   SKILL.md, reference.md, listings_template.csv, scripts/
  peru-safe-investments/  SKILL.md, reference.md, scripts/
  rent-vs-buy-model/      SKILL.md, reference.md
  streamlit-dashboard/    SKILL.md, reference.md
.claude/agents/           market-data.md, opportunity-cost.md, financial-analysis.md, streamlit-builder.md
salidas/validacion.txt
figuras/
tests/
evaluacion.md  README.md  pyproject.toml  instalar.py
```

No hay `mapas/`: el proyecto no dibuja mapas porque no tiene límites distritales de Lima. Es el siguiente paso natural
(un mapa del veredicto por distrito).

## Supuestos y decisiones

- Horizontes de 5, 10, 15, 20 y 30 años; el plazo del préstamo es otro parámetro, 20 años por defecto (editable).
- Tasas hipotecarias: promedio de mercado de −2 a +2 puntos.
- Veredicto: «comprar» si comprar gana en el 80 % o más de los escenarios, «alquilar» si gana en el 20 % o menos,
  «depende» en otro caso.
- «Fondo a plazo» se lee como depósito a plazo en soles; «Bolsa de Perú» como el S&P/BVL Peru General.
- El S&P 500 se pasa a soles con una variación USD/PEN supuesta, 0 % al año por defecto (editable).
- Se supone que el inquilino paga el mantenimiento, como es común en Lima, así que se cancela.
- Los supuestos están comentados en `.claude/skills/buy-vs-rent/scripts/housing_lima/config/defaults.yaml`.
- No se modelan subsidios (Bono del Buen Pagador); `housing_lima/subsidy.py` deja el punto de extensión.

## Si se atascan

| Síntoma | Qué hacer |
|---|---|
| `/buy-vs-rent` no aparece | Corran `python instalar.py`, reinicien Claude Code y escriban `/skills`. En el repositorio, abran Claude Code dentro de `Skill_Buy_Rent/` |
| La skill no se activa sola | Llámenla con `/buy-vs-rent` o usen palabras de la `description`: comprar, alquilar, Lima |
| Los agentes no se lanzan | Revisen que estén en `~/.claude/agents/` o `.claude/agents/` y escriban `/agents`. Si no hay agentes, el orquestador hace los pasos él mismo |
| Los portales bloquean la búsqueda | Copien `listings_template.csv` a `datos/listings.csv`, peguen los avisos con su URL y fecha y repitan; la corrida sale como `csv` |
| `check-env` dice que falta un paquete | `uv sync` o `pip install -e .` en esta carpeta |
| Un distrito sale con «baja confianza» | Hubo menos de 8 avisos de venta o de alquiler; amplíen el rango o quiten el distrito |
| En claude.ai (chat web) no funciona | Las skills de claude.ai corren en un contenedor sin internet ni sus paquetes; úsenla en Claude Code |
