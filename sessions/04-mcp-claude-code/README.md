# Sesión 04 · MCP: Claude conectado a sus datos

Qué es el Model Context Protocol, qué servidores existen y en cuáles confiar, cómo se usan en Claude Code y cómo se
construye uno propio con FastMCP. Basada en el curso corto «MCP: Build Rich-Context AI Apps with Anthropic» de
DeepLearning.AI, llevado a Claude Code.

**Slides de la clase:** https://claude.ai/artifact/B9W8izJCRr6qsTLwbMXqcT

| Bloque | Duración | Qué se hace |
|---|---|---|
| Explicación y demo | 60 min | Arquitectura, primitivas y transportes; el catálogo de servidores; `claude mcp add` y sus alcances; seguridad; FastMCP |
| Proyecto | 1 h 40 min | Un MCP con las 17,167 series del BCRP, probado, conectado a Claude Code y evaluado con `claude -p` |
| Resultados | 20 min | Tres repositorios al azar: ¿cuántas cifras acertó Claude sin su MCP y cuántas con él? |

## Contenido

| Carpeta | Qué hay |
|---|---|
| [`proyecto/`](proyecto/) | El enunciado, el servidor inicial, las 8 pruebas, las preguntas y el script de evaluación |
| [`mcps_mas_usados.md`](mcps_mas_usados.md) | Los MCP con más estrellas y descargas, los que sirven para datos y cómo repetir la medición |

## Entorno

El proyecto lleva su propio `pyproject.toml` (FastMCP 4, httpx y pandas), fuera del entorno del curso:

```bash
cd sessions/04-mcp-claude-code/proyecto
uv run pytest -q          # crea el entorno la primera vez
```

Necesitan Claude Code con su sesión iniciada. Node solo hace falta para MCP Inspector y los servidores que se instalan
con `npx`.

## Relacionado

[`sessions/11-agentes/lab/Skills_Claude/`](../11-agentes/lab/Skills_Claude/) tiene un MCP del BCRP más chico, con seis
series fijas, que una skill de Claude Code convierte en un dashboard de Streamlit.
