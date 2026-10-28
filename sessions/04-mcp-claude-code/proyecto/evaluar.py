"""¿Inventa cifras Claude? Las mismas preguntas sin herramientas y con su MCP, contra la cifra oficial.

    uv run evaluar.py                                   # memoria y mcp, con Haiku
    uv run evaluar.py --modos memoria mcp web --modelo sonnet

Cada pregunta se le hace a Claude Code en modo no interactivo (claude -p) y debe responder un JSON con el valor.
Escribe resultados.csv y cuenta cuántas acierta, cuántas se equivoca y en cuántas reconoce que no sabe.
"""
import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "unidad": {"type": "string"},
                          "fuente": {"type": "string"}}}
INSTRUCCION = ("Responde con un solo número en «valor», en la unidad que pide la pregunta. Si no puedes saberlo "
               "con certeza, pon valor null: no estimes. En «fuente» di de dónde sale la cifra.\n\n")
MODOS = {   # todas sin las herramientas de archivos y terminal de Claude Code
    "memoria": ["--tools", "", "--strict-mcp-config"],
    "web": ["--tools", "WebSearch,WebFetch", "--allowedTools", "WebSearch,WebFetch", "--strict-mcp-config"],
    "mcp": ["--tools", "", "--strict-mcp-config", "--mcp-config", str(AQUI / ".mcp.json"), "--allowedTools", "mcp__bcrp"],
}


def preguntar(pregunta, modo, modelo):
    cmd = ["claude", "-p", INSTRUCCION + pregunta, "--output-format", "json", "--json-schema", json.dumps(ESQUEMA),
           "--no-session-persistence", "--model", modelo, *MODOS[modo]]
    t = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=AQUI)
    try:
        salida = json.loads(proc.stdout)
    except json.JSONDecodeError:
        salida = {"result": (proc.stdout + proc.stderr)[-300:]}
    r = salida.get("structured_output") or {}
    return {"valor": r.get("valor"), "fuente": r.get("fuente", salida.get("result", "")),
            "segundos": round(time.time() - t, 1), "turnos": salida.get("num_turns")}


def calificar(valor, verdad, tolerancia):
    if valor is None:
        return "no sabe"
    return "acierta" if abs(valor - verdad) <= tolerancia else "se equivoca"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=["memoria", "mcp"], choices=list(MODOS))
    p.add_argument("--modelo", default="haiku")
    p.add_argument("--preguntas", default=str(AQUI / "preguntas.csv"))
    p.add_argument("--paralelo", type=int, default=4)
    a = p.parse_args()
    if "mcp" in a.modos and not (AQUI / ".mcp.json").exists():
        raise SystemExit("Falta .mcp.json. Conecten su servidor: claude mcp add --scope project bcrp -- uv run server.py")

    preguntas = pd.read_csv(a.preguntas)
    casos = [(q, m) for q in preguntas.itertuples() for m in a.modos]
    print(f"{len(casos)} llamadas a claude -p con {a.modelo}...")
    with ThreadPoolExecutor(a.paralelo) as ex:
        respuestas = list(ex.map(lambda c: preguntar(c[0].pregunta, c[1], a.modelo), casos))

    filas = [{"id": q.id, "modo": m, "verdad": q.verdad, **r, "resultado": calificar(r["valor"], q.verdad, q.tolerancia)}
             for (q, m), r in zip(casos, respuestas)]
    res = pd.DataFrame(filas)
    res.to_csv(AQUI / "resultados.csv", index=False)

    print("\n" + res.pivot(index="id", columns="modo", values="valor").to_string())
    tabla = res.groupby("modo").resultado.value_counts().unstack(fill_value=0)
    tabla["segundos"] = res.groupby("modo").segundos.mean().round(1)
    print("\n" + tabla.to_string())
