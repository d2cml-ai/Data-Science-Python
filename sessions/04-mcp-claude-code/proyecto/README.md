# Proyecto · Un MCP con las series oficiales del BCRP

En 1 h 40 min construyen un servidor MCP con FastMCP que busca entre las 17,167 series del Banco Central de Reserva
del Perú, las descarga y calcula variaciones. Después lo conectan a Claude Code y miden, con `claude -p`, cuántas cifras
acierta Claude sin su servidor y cuántas con él.

| Archivo | Qué es |
|---|---|
| `server.py` | El servidor. `buscar_series` ya funciona; faltan los TODO 1 a 5 |
| `test_server.py` | El contrato: 8 pruebas con datos reales del BCRP. No lo cambien |
| `preguntas.csv` | 8 preguntas con la cifra oficial y la tolerancia; ustedes agregan 2 |
| `evaluar.py` | Le hace cada pregunta a Claude sin herramientas y con su MCP, y califica |

Necesitan `uv`, Claude Code con su sesión iniciada e internet. Node solo hace falta para MCP Inspector, que es opcional.

## Parte 0 · Preparar (10 min)

```bash
git clone https://github.com/d2cml-ai/Data-Science-Python      # o git pull si ya lo tienen
cp -r Data-Science-Python/sessions/04-mcp-claude-code/proyecto mcp-bcrp
cd mcp-bcrp && git init

uv run pytest -q                                               # esperado: 1 passed, 7 failed

claude mcp add --transport http fastmcp-docs https://gofastmcp.com/mcp
claude
```

`uv run` crea el entorno la primera vez. La primera prueba baja el catálogo del BCRP (unos 7 MB) a `datos/`, que git
ignora. El MCP `fastmcp-docs` le da a Claude la documentación de FastMCP 4, más nueva que lo que el modelo aprendió.

Un buen primer mensaje: *«Lee server.py y test_server.py. Antes de escribir código, explícame qué pide el TODO 1 y qué
formato de fechas usa la API.»* Claude puede escribir el código, pero ustedes tienen que poder explicar cada línea.

## Parte 1 · Servidor (35 min)

Completen los TODO de `server.py` en orden. El comentario de cada uno trae lo que necesitan saber de la API.

| TODO | Qué agregan | Prueba que lo revisa |
|---|---|---|
| 1 | `serie(codigo, desde, hasta)`: los datos y la URL de la fuente | `test_serie_mensual`, `test_serie_diaria`, `test_codigo_inexistente_da_un_error_claro` |
| 2 | `resumen(codigo, desde, hasta)`: primero, último, cambio, variación, promedio, máximo y mínimo | `test_resumen_sin_cuentas_a_mano` |
| 3 | Una herramienta suya, con un docstring que diga cuándo usarla | `test_cuatro_herramientas_como_minimo` |
| 4 | Un recurso, por ejemplo `bcrp://serie/{codigo}` | `test_un_recurso` |
| 5 | Un prompt, por ejemplo `informe(tema)` | `test_un_prompt` |

```bash
uv run pytest -q -k serie        # solo las pruebas de serie
uv run pytest -q                 # todas: la meta es 8 passed
```

El TODO 1 es el más largo: los meses llegan como `Ene.2025`, los días como `01.Oct.26` y setiembre viene escrito
`Set`. Si a los 35 minutos no tienen 8 de 8, pasen igual a la parte 2: con `buscar_series` y `serie` ya se puede evaluar.

Para ver qué devuelve una herramienta sin pasar por Claude:

```python
import asyncio
from fastmcp import Client
from server import mcp

async def main():
    async with Client(mcp) as c:
        r = await c.call_tool("serie", {"codigo": "PN01273PM", "desde": "2026-01", "hasta": "2026-09"})
        print(r.data)

asyncio.run(main())
```

Con Node instalado, `npx @modelcontextprotocol/inspector uv run server.py` abre una página para llamar cada
herramienta a mano.

## Parte 2 · Conectar (10 min)

```bash
claude mcp add --scope project bcrp -- uv run server.py
claude mcp add --scope project fetch -- uvx mcp-server-fetch
cat .mcp.json
```

Abran `claude` en la carpeta. Si les pregunta si aprueban los servidores de `.mcp.json`, acepten: son los suyos. Prueben:

1. `/mcp`: los dos servidores conectados, con sus herramientas.
2. Una pregunta, por ejemplo *«¿Cuál fue la inflación de Lima a 12 meses en setiembre de 2026?»*. Revisen en el detalle
   que Claude llamó a `buscar_series` y luego a `resumen` o `serie`, en vez de calcular a mano.
3. Un recurso: `@bcrp:bcrp://serie/PN01273PM ¿desde cuándo hay datos de esta serie?`
4. Un prompt: `/mcp__bcrp__informe inflación`
5. Fetch: *«Lee https://gofastmcp.com/llms.txt y dime qué secciones tiene la documentación de FastMCP.»*

## Parte 3 · Evaluar (25 min)

1. Agreguen 2 filas a `preguntas.csv` sobre series que les interesen (empleo, exportaciones, crédito, depósitos,
   precios de metales...). Saquen la `verdad` de [estadisticas.bcrp.gob.pe](https://estadisticas.bcrp.gob.pe), no de su
   propio MCP, y pongan una `tolerancia` de redondeo: 0.05 para porcentajes, algo mayor para montos grandes.
2. Corran la evaluación. Con 10 preguntas en dos modos tarda uno o dos minutos:

   ```bash
   uv run evaluar.py                  # memoria contra mcp, con Haiku; escribe resultados.csv
   ```

   Si el BCRP empieza a responder «no respondió con datos», bajen el paralelismo con `--paralelo 2`.
3. Experimento extra, para el cuarto punto de la evaluación. Antes guarden la corrida base con
   `cp resultados.csv resultados_base.csv`, y luego elijan uno:
   - **Sin salida fácil:** en `evaluar.py`, borren de `INSTRUCCION` la frase «Si no puedes saberlo con certeza, pon
     valor null: no estimes.» y vuelvan a correr. ¿Claude sigue diciendo que no sabe, o inventa una cifra?
   - **Contra la búsqueda web:** `uv run evaluar.py --modos memoria web mcp`. Cada pregunta con web tarda unos 25 s.

Para referencia, con las 8 preguntas del archivo y Haiku: memoria 0 de 8 (8 «no sé»), web 7 de 8, MCP 8 de 8.

## Parte 4 · Informe (15 min)

Escriban `informe.md` con:

- La tabla de `resultados.csv`: aciertos, errores y «no sé» por modo, y los segundos promedio.
- Qué preguntas falló cada modo y por qué. La columna `fuente` dice de dónde sacó Claude cada cifra.
- Dos cifras de su MCP comprobadas a mano en la web del BCRP, con el link de la tabla donde las vieron.
- Una figura, `grafico.png`. Para usar matplotlib: `uv add matplotlib`. Sirve el porcentaje de aciertos por modo o la
  serie que usa su herramienta propia.
- Tres a cinco líneas de conclusión: ¿cuándo vale la pena construir un MCP y cuándo basta la búsqueda web?

Luego `git add`, `git commit`, creen el repositorio en GitHub, hagan `git push` y peguen el link en el issue de la sesión.

## Entrega

`server.py`, `test_server.py` sin cambios, `.mcp.json`, `preguntas.csv` con 10 preguntas, `resultados.csv`,
`informe.md` y `grafico.png`. La carpeta `datos/` no se sube: se vuelve a bajar sola.

## Rúbrica (20 puntos)

| Criterio | Puntos | Qué se mira |
|---|---|---|
| Pruebas | 6 | 8 de 8 en verde; un punto menos por cada prueba que falle |
| Herramienta propia | 3 | Útil, con un docstring que diga cuándo usarla, y con su fuente en la respuesta |
| Recurso y prompt | 2 | Funcionan en Claude Code con `@` y con `/` |
| `.mcp.json` | 2 | En el repo, con `bcrp` y `fetch`, y sin claves |
| Evaluación | 4 | 10 preguntas, dos suyas con la verdad revisada a mano (3); un experimento extra (1) |
| Informe | 3 | Qué acertó y qué no, por qué, una figura y dos cifras comprobadas en la web del BCRP |

## Si se atascan

| Síntoma | Qué hacer |
|---|---|
| «El BCRP no respondió con datos» | La API limita los pedidos seguidos. Esperen unos segundos y reintenten; guarden en caché lo que ya bajaron |
| `/mcp` muestra `bcrp` con error | Corran `uv run pytest -q` para ver el error de Python, o `claude mcp get bcrp` para ver el comando |
| Claude no usa su herramienta | Mejoren el docstring: qué hace, cuándo usarla y un ejemplo de argumentos |
| Claude escribe código de FastMCP 2 | Pídanle que consulte `fastmcp-docs` antes de responder |
