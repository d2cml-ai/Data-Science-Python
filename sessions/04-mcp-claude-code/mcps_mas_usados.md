# Los MCP más usados

Medido el 28 de octubre de 2026. No hay un ranking oficial de uso, así que se miran dos cosas:

- **Estrellas en GitHub**: miden interés, no uso.
- **Descargas de la última semana** en npm o PyPI: se acercan más al uso real, aunque están algo infladas porque
  `npx …@latest` vuelve a bajar el paquete en cada arranque y porque cuentan las corridas de CI.

Quedan fuera las listas (`punkpeye/awesome-mcp-servers` tiene 97 mil estrellas) y las aplicaciones que solo traen un MCP
como extra. «—» quiere decir que no hay dato de npm ni de PyPI.

## En general

| Repositorio | Qué hace | ★ GitHub | Descargas/semana |
|---|---|---|---|
| `modelcontextprotocol/servers` | Los de referencia: Fetch, Filesystem, Git, Memory, Time | 91.6k | Filesystem 911k, Fetch 247k |
| `upstash/context7` | Documentación al día de librerías | 63.9k | 478k |
| `ChromeDevTools/chrome-devtools-mcp` | Depurar páginas en Chrome | 54.4k | 2.95 M |
| `DeusData/codebase-memory-mcp` | Índice local del código para agentes | 47.7k | — |
| `microsoft/playwright-mcp` | Un navegador que Claude maneja | 38.8k | **6.9 M** |
| `github/github-mcp-server` | Issues, pull requests y código; el oficial | 34.0k | — |
| `mksglu/context-mode` | Recorta lo que devuelven las herramientas para ahorrar contexto | 32.7k | — |
| `ahujasid/mcp-for-blender` | Controlar Blender 3D | 32.6k | 60k |
| `oraios/serena` | Buscar y editar código por símbolos (funciones, clases) | 30.8k | 44k |
| `eyaltoledano/claude-task-master` | Gestor de tareas; sin cambios desde abril de 2026 | 28.3k | 12k |
| `czlonkowski/n8n-mcp` | Armar flujos de n8n | 23.2k | 115k |
| `googleapis/mcp-toolbox` | Bases de datos: Postgres, BigQuery y otras | 16.7k | — |
| `GLips/Figma-Context-MCP` | Diseños de Figma convertidos en código | 16.1k | 112k |
| `apify/apify-mcp-server` | Scrapers listos: redes sociales, Google Maps | 13.7k | 21k |
| `wonderwhy-er/DesktopCommanderMCP` | Terminal y archivos | 10.2k | 637k |
| `awslabs/mcp` | Servidores de AWS | 9.8k | documentación 68k |

## Para investigar y analizar datos

| Repositorio | Para qué | ★ GitHub | Descargas/semana |
|---|---|---|---|
| `microsoft/markitdown` (`markitdown-mcp`) | PDF, Word, Excel y PowerPoint a markdown | 193k (la herramienta) | 31k |
| `sooperset/mcp-atlassian` | Jira y Confluence | 6.1k | 221k |
| `firecrawl/firecrawl-mcp-server` | Scraping y búsqueda web | 7.7k | 152k |
| `taylorwilsdon/google_workspace_mcp` | Gmail, Calendar, Docs y Sheets | 3.4k | 101k |
| `haris-musa/excel-mcp-server` | Crear y editar Excel con gráficos | 4.3k | 45k |
| `dbt-labs/dbt-mcp` | Modelos de dbt | 614 | 26k |
| `blazickjp/arxiv-mcp-server` | Buscar, bajar y leer papers de arXiv | 3.2k | 20k |
| `datalayer/jupyter-mcp-server` | Leer, editar y ejecutar notebooks | 1.3k | 12k |
| `54yyyu/zotero-mcp` | Su biblioteca de Zotero | 5.6k | — |

El comando de instalación está en el README de cada repositorio. MarkItDown (Microsoft), Firecrawl y dbt son de la
empresa del producto; el resto es de la comunidad, incluido el de Atlassian. Apliquen las cinco preguntas de la clase
antes de instalarlos, sobre todo el de Google Workspace, que lee su correo.

## Lo que dicen los datos

- **En Claude Code, varios de los más descargados sobran.** Filesystem y Desktop Commander dan archivos y terminal, que
  Claude Code ya tiene; sirven en Claude Desktop. En Claude Code valen la pena los que agregan algo que no tiene: un
  navegador, documentación al día, servicios externos o bases de datos.
- **Hay servidores archivados que se siguen descargando mucho.** Los de referencia de Postgres (156k por semana),
  GitHub (155k) y Slack (125k) ya no reciben correcciones de seguridad. Usen el oficial de cada empresa, por ejemplo
  `github/github-mcp-server`.
- **Las estrellas solas no bastan para confiar.** En la búsqueda por tema de GitHub aparecen repositorios con cifras que
  no cuadran con lo conocidos que son. Antes de instalar, miren quién lo mantiene y cuándo cambió por última vez.

## Cómo repetir la medición

```bash
# estrellas, última actividad y si está archivado
gh api repos/microsoft/playwright-mcp --jq '.stargazers_count, .pushed_at, .archived'

# descargas de la última semana en npm
curl -s https://api.npmjs.org/downloads/point/last-week/@playwright/mcp

# descargas de la última semana en PyPI
curl -s https://pypistats.org/api/packages/mcp-server-fetch/recent

# los repositorios con más estrellas de un tema
gh search repos "topic:mcp-server" --sort stars --limit 40 --json fullName,stargazersCount
```
