# Sesión 16 · Skills de Claude Code: limpiar, graficar y mapear la ENAHO

Qué es una skill de Claude Code, por qué conviene crearla dentro del repositorio y cómo se arma una que limpie la ENAHO
siempre de la misma forma. El proyecto son tres skills que trabajan juntas: una limpia los módulos del INEI, otra
hace gráficos y otra hace un mapa por departamento.

**Slides de la clase:** https://claude.ai/artifact/X7H6PUvaWKde1epsYCJNze

| Bloque | Duración | Qué se hace |
|---|---|---|
| Clase | 30 min | Qué es una skill, cómo se carga y se activa, por qué en Claude Code, el pipeline de la ENAHO y sus trampas |
| Proyecto | 45 min | Tres skills: `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`, validadas y probadas con y sin ellas |
| Presentaciones | 15 min | Cuatro repositorios al azar, tres minutos cada uno |

## Contenido

| Archivo | Qué hay |
|---|---|
| [`referencias/pobreza_departamento_2024.csv`](referencias/pobreza_departamento_2024.csv) | La pobreza 2024 de los 25 departamentos, para validar el mapa |
| [`referencias/mapa_pobreza_2024.png`](referencias/mapa_pobreza_2024.png) | Cómo debe verse el mapa |

## Lo esencial de una skill

- **Es una carpeta** con un `SKILL.md` obligatorio y, si hace falta, archivos de referencia y scripts. En un proyecto
  va en `.claude/skills/<nombre>/`. Así viaja con git y todo el equipo usa la misma.
- **`SKILL.md`** empieza con un bloque YAML con `name` (minúsculas, números y guiones; hasta 64 caracteres) y
  `description`. Debajo van las instrucciones, en menos de 500 líneas.
- **Carga progresiva.** Al inicio Claude solo ve `name` y `description` de cada skill, unos 100 tokens. El cuerpo se
  carga cuando la tarea lo pide, y los demás archivos solo si se usan. De un script solo entra al contexto lo que
  imprime.
- **Se activa sola** cuando un pedido coincide con la `description`, o a mano con `/nombre argumentos`. Dentro del
  archivo, `$ARGUMENTS` o `$0` toman los argumentos, y `${CLAUDE_SKILL_DIR}` es la carpeta de la skill.
- **La `description`** se escribe en tercera persona y dice qué hace y cuándo usarla, con las palabras que usaría
  quien la pide: ENAHO, INEI, pobreza, mapa.
- **Script o instrucción.** Lo que no se discute (llaves, filtros, uniones, validación) va en un script que la skill
  corre tal cual. Lo que requiere criterio va en el texto.

### Por qué crearla en Claude Code

1. Se versiona con git y los cambios se revisan en un pull request.
2. Corre en su máquina, con su entorno de `uv`, sus archivos e internet. En la API de Claude las skills corren en un
   contenedor sin red y sin poder instalar paquetes.
3. El script hace que el resultado sea el mismo cada vez y para cualquiera.
4. Se puede evaluar con `claude -p`, con y sin skills.
5. Se combina con MCP, hooks y subagentes en el mismo proyecto.
6. Sigue el estándar abierto Agent Skills: la misma carpeta se puede subir a claude.ai como zip.

## Los datos

| Archivo | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|
| [Módulo 34, sumaria](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip) (16 MB) | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` |
| [Módulo 02, miembros](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip) (6 MB) | persona | 117,721 | las tres + `codperso` | `facpob07` |
| [Límites departamentales](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson) (140 KB) | departamento | 25 | `FIRST_IDDP` | — |

`966` es el código de la ENAHO 2024 en el portal de microdatos del INEI. Bájenlos desde el navegador a una carpeta
`datos/` y pónganla en `.gitignore`.

## El proyecto

Tres skills en `.claude/skills/` de un repositorio nuevo:

| Skill | Entra | Sale |
|---|---|---|
| `limpiando-enaho` | Los zip de los módulos 34 y 02 | `salidas/personas_2024.parquet` y `salidas/validacion.txt` |
| `graficando-enaho` | La base limpia y una pregunta: pobreza por área, sexo o edad | `figuras/*.png` |
| `mapeando-enaho` | La base limpia y el GeoJSON | `mapas/pobreza_departamento.png` |

En las skills de gráficos y mapas escriban: «Si no existe `salidas/personas_2024.parquet`, usa primero la skill
`limpiando-enaho`». Así un solo pedido activa dos skills seguidas.

### 1. Preparar (0–8 min)

```bash
mkdir enaho-skills && cd enaho-skills && git init
uv init
uv add pandas pyarrow geopandas matplotlib
mkdir -p datos .claude/skills
echo "datos/" >> .gitignore
```

### 2. Limpiar (8–20 min)

El pipeline de `scripts/limpiar.py`, siempre en este orden:

1. **Leer** con `pd.read_stata(..., convert_categoricals=False)` y las llaves como texto.
2. **Normalizar** los nombres de columna a minúscula. La columna del año llega como `aÑo`.
3. **Filtrar** a los residentes habituales: `(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`.
4. **Unir** personas y hogares con `merge(..., validate="m:1")`.
5. **Construir** `departamento = ubigeo[:2]`, `urbano = estrato <= 5` y `pobre = pobreza <= 2`.
6. **Validar** que las llaves sean únicas, que la unión no pierda ni duplique filas y que la pobreza dé 27.6 %.
7. **Guardar** `salidas/personas_2024.parquet` y `salidas/validacion.txt`.

Un primer pedido a Claude Code:

> Escribe scripts/limpiar.py según este pipeline: lee datos/966-Modulo34 y 966-Modulo02, filtra residentes
> habituales, une con validate="m:1" y termina con asserts que comprueben la pobreza oficial de 2024.

La skill, como referencia:

```markdown
---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, sexo o edad.
argument-hint: [año]
---
# Limpiar la ENAHO
1. Si faltan los zip en datos/, pide al usuario bajarlos del INEI (código 966 = 2024).
2. Corre exactamente: uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0
3. Lee salidas/validacion.txt. Si la pobreza difiere del INEI en más de 0.1 puntos, detente.
4. Responde con salidas/personas_$0.parquet; toda cifra va ponderada con facpob07.
5. Antes de usar una variable que no está en la base, lee reference.md.
```

### 3. Graficar y mapear (20–32 min)

| `graficando-enaho` | `mapeando-enaho` |
|---|---|
| Pondera siempre con `facpob07` | Une por código: `ubigeo[:2]` con `FIRST_IDDP` |
| Barras que empiezan en cero, ordenadas | Nunca por nombre: «APURIMAC» no es «Apurímac» |
| Un solo color y el valor escrito en cada barra | Exige 25 departamentos y ninguno sin dato |
| El título dice qué y cuándo | Un color de claro a oscuro, desde 0; nunca arcoíris |
| Nota al pie: «Fuente: INEI, ENAHO 2024» | Leyenda con la unidad: % de personas |
| PNG a 200 dpi en `figuras/` | Lima (15) y Callao (07) van separados |

### 4. Evaluar y subir (32–45 min)

Corran tres pedidos con y sin skills y anoten en `evaluacion.md` qué skills se activaron, la cifra, si ponderó y cómo
se ve la figura:

```bash
claude -p "Haz un mapa de la pobreza por departamento con la ENAHO 2024"                        # con skills
claude -p --disallowedTools Skill "Haz un mapa de la pobreza por departamento con la ENAHO 2024"  # sin skills
```

| Pedido | Skills que deberían activarse | Lo que debe salir |
|---|---|---|
| ¿Cuál fue la pobreza en Cusco en 2024? | `limpiando-enaho` | 18.5 % |
| Grafica la pobreza urbana y rural | `graficando-enaho` (+ `limpiando-enaho`) | 24.8 % y 39.3 % |
| Haz un mapa de la pobreza por departamento | `mapeando-enaho` (+ `limpiando-enaho`) | Cajamarca 45.0 %, Ica 6.0 % |

Si una skill no se activa, mejoren su `description` y repitan. Al final, `git push` y peguen el link en el issue de la
sesión.

## Validación

Calculado con los archivos 2024 del INEI:

| Cifra | Valor |
|---|---|
| Pobreza monetaria nacional | 27.6 % (27.58 % con la sumaria y `factor07 × mieperho`; 27.53 % con personas y `facpob07`) |
| Pobreza extrema | 5.5 % |
| Hogares en la sumaria | 33,691 |
| Residentes habituales | 108,664 de 117,721 filas del módulo 02 |
| Urbano / rural (`estrato <= 5`) | 24.8 % / 39.3 % |
| Lima Metropolitana (`dominio == 8`) | 28.2 % |

La pobreza de cada departamento está en [`referencias/pobreza_departamento_2024.csv`](referencias/pobreza_departamento_2024.csv).

## Entrega

```text
.claude/skills/
  limpiando-enaho/   SKILL.md, reference.md, scripts/limpiar.py
  graficando-enaho/  SKILL.md, scripts/
  mapeando-enaho/    SKILL.md, scripts/
salidas/validacion.txt
figuras/  mapas/
evaluacion.md  README.md  pyproject.toml
```

| Criterio | Puntos |
|---|---|
| Limpieza: valida 27.6 % y 108,664 personas | 6 |
| `graficando-enaho` con sus reglas | 4 |
| `mapeando-enaho`: une por código, 25 departamentos con dato | 4 |
| Tres pedidos con y sin skills | 4 |
| README que explica cómo bajar los datos y correr todo | 2 |

En las presentaciones muestren su mapa y un gráfico, su `validacion.txt` y un pedido que activó dos skills seguidas.

## Para explorar

| Repositorio | ★ (31 oct. 2026) | Qué tiene |
|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | 185.7k | Las oficiales: xlsx, docx, pptx, pdf y skill-creator |
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | 34.1k | Plugin `data`: explore-data, validate-data, sql-queries |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 55.5k | 177 de ciencia: EDA, statsmodels, scikit-learn, geopandas, matplotlib |
| [huggingface/skills](https://github.com/huggingface/skills) | 11.2k | Datasets, entrenar LLM, modelos locales y Gradio |
| [obra/superpowers](https://github.com/obra/superpowers) | 309.7k | Forma de trabajar: depurar, planes, TDD, writing-skills |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 78.4k | Lista curada, por categoría |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 36.7k | Más de mil skills de equipos oficiales y comunidad |

```bash
/plugin marketplace add anthropics/skills                          # dentro de Claude Code
/plugin install document-skills@anthropic-agent-skills
claude plugin marketplace add anthropics/knowledge-work-plugins     # desde la terminal
```

Una skill puede ejecutar scripts en su máquina: lean su `SKILL.md` y sus scripts antes de instalarla. Las estrellas no
bastan para confiar; hay repositorios creados en 2026 con más estrellas que el de Anthropic.

## Si se atascan

| Síntoma | Qué hacer |
|---|---|
| La skill no aparece | Revisen que esté en `.claude/skills/<nombre>/SKILL.md` y escriban `/skills`. Si crearon la carpeta `.claude/skills` con Claude Code abierto, reinícienlo |
| La skill no se activa sola | Agreguen a la `description` las palabras del pedido (ENAHO, pobreza, mapa) o llámenla con `/nombre` |
| La pobreza no da 27.6 % | Revisen que ponderen y que filtren residentes habituales |
| Un departamento sale en blanco | La unión fue por nombre o el código perdió el cero: unan `ubigeo[:2]` con `FIRST_IDDP` como texto |
| El YAML no se lee | Los `---` deben ser la primera línea, sin espacios antes |

## Fuentes

- [Skills en Claude Code](https://code.claude.com/docs/en/skills)
- [Agent Skills: overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Agent Skills: best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
