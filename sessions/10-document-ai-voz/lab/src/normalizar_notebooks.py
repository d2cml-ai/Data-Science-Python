"""normalizar_notebooks.py — arregla notebooks con las lineas pegadas.

El problema que resuelve, que ya costo una sesion entera:

    El campo `source` de una celda es una lista de cadenas, y el formato exige que
    cada una termine en salto de linea menos la ultima. Si faltan los saltos, al
    unirlas el codigo queda pegado:

        import matplotlib.pyplot as pltpagina = mitades[0]fig, ejes = ...

    Jupyter y VS Code lo toleran y lo muestran bien, asi que el notebook parece
    sano y se puede editar y ejecutar sin notar nada. Pero `nbconvert --execute`,
    Colab y cualquier herramienta que siga el formato al pie de la letra ven una
    sola linea y revientan con `SyntaxError: invalid syntax`.

    Es decir: el notebook funciona en la maquina de quien lo escribio y falla en la
    de los 25 estudiantes. Ese es exactamente el fallo que no se puede permitir.

Ademas revisa que cada celda de codigo compile, y puede borrar las salidas antes de
publicar. Las salidas guardadas son un problema de verdad: quedan dentro del .ipynb y
viajan al repositorio con el, y suelen traer rutas locales (`C:\\Users\\<quien sea>`),
fragmentos de claves que alguna celda imprimio, e imagenes en base64 que inflan el
archivo de 20 KB a medio mega.

Correr antes de cada entrega:

    python -m src.normalizar_notebooks              # arregla formato
    python -m src.normalizar_notebooks --revisar    # solo avisa, no escribe
    python -m src.normalizar_notebooks --limpiar    # ademas borra las salidas
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.comun import RAIZ, configurar_logging

log = configurar_logging("normalizar_notebooks")


def celdas_malformadas(notebook: dict) -> list[int]:
    """Indices de las celdas cuyo `source` no lleva los saltos de linea."""
    malas = []
    for indice, celda in enumerate(notebook.get("cells", [])):
        fuente = celda.get("source")
        if not isinstance(fuente, list) or len(fuente) <= 1:
            continue
        if not all(linea.endswith("\n") for linea in fuente[:-1]):
            malas.append(indice)
    return malas


def normalizar_celda(celda: dict) -> bool:
    """Deja el `source` de una celda en el formato correcto. Devuelve si cambio.

    Se reconstruye desde el texto completo: se unen las partes con salto de linea
    cuando faltan, y se vuelve a partir dejando el salto al final de cada una.
    """
    fuente = celda.get("source")
    if not isinstance(fuente, list) or len(fuente) <= 1:
        return False
    if all(linea.endswith("\n") for linea in fuente[:-1]):
        return False

    # Si ninguna lleva salto, cada elemento era una linea suelta.
    texto = "".join(fuente) if any("\n" in l for l in fuente) else "\n".join(fuente)

    lineas = texto.split("\n")
    celda["source"] = [l + "\n" for l in lineas[:-1]] + [lineas[-1]]
    return True


def celdas_que_no_compilan(notebook: dict) -> list[tuple[int, str]]:
    """Celdas de codigo con error de sintaxis, como (indice, mensaje).

    Se saltan las celdas con magics de IPython (`%pip`, `!comando`): son validas en
    Jupyter pero `ast.parse` no las entiende, y marcarlas seria un falso positivo.

    Este chequeo existe porque un notebook puede guardarse con un string partido a
    la mitad y verse bien en el editor: el error solo aparece cuando alguien lo
    ejecuta. Que eso pase en el salon, con 25 personas mirando, no es aceptable.
    """
    import ast

    malas: list[tuple[int, str]] = []
    for indice, celda in enumerate(notebook.get("cells", [])):
        if celda.get("cell_type") != "code":
            continue
        fuente = "".join(celda.get("source", []))
        if any(l.strip().startswith(("!", "%")) for l in fuente.splitlines()):
            continue
        try:
            ast.parse(fuente)
        except SyntaxError as e:
            malas.append((indice, f"{e.msg} (linea {e.lineno})"))
    return malas


def limpiar_salidas(notebook: dict) -> int:
    """Borra las salidas guardadas de todas las celdas. Devuelve cuantas limpio."""
    limpiadas = 0
    for celda in notebook.get("cells", []):
        if celda.get("cell_type") != "code":
            continue
        if celda.get("outputs") or celda.get("execution_count") is not None:
            celda["outputs"] = []
            celda["execution_count"] = None
            limpiadas += 1
    return limpiadas


def normalizar_notebook(ruta: Path, escribir: bool = True,
                        limpiar: bool = False) -> int:
    """Normaliza un notebook. Devuelve cuantas celdas arreglo."""
    notebook = json.loads(ruta.read_text(encoding="utf-8"))

    arregladas = sum(normalizar_celda(c) for c in notebook.get("cells", []))

    if limpiar:
        salidas = limpiar_salidas(notebook)
        if salidas:
            log.info("%s: %d salidas borradas", ruta.name, salidas)
            arregladas += salidas

    if (arregladas or limpiar) and escribir:
        ruta.write_text(
            json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        log.info("%s: %d celdas arregladas", ruta.name, arregladas)
    elif arregladas:
        log.warning("%s: %d celdas MALFORMADAS (no se escribio nada)",
                    ruta.name, arregladas)
    else:
        log.info("%s: formato correcto", ruta.name)

    # Normalizar los saltos no garantiza que el codigo compile: un string partido a
    # la mitad sobrevive a la normalizacion. Por eso se revisa tambien la sintaxis.
    for indice, mensaje in celdas_que_no_compilan(notebook):
        log.error("%s, celda %d NO COMPILA: %s", ruta.name, indice, mensaje)

    return arregladas


def ejecutar(escribir: bool = True, limpiar: bool = False) -> int:
    """Recorre notebooks/ y normaliza lo que haga falta."""
    carpeta = RAIZ / "notebooks"
    rutas = sorted(carpeta.glob("*.ipynb"))
    if not rutas:
        log.warning("No hay notebooks en %s", carpeta)
        return 0

    total = sum(normalizar_notebook(r, escribir, limpiar) for r in rutas)

    print()
    if total == 0:
        print(f"Los {len(rutas)} notebooks estan bien formados.", flush=True)
    elif escribir:
        print(f"{total} celdas arregladas en {len(rutas)} notebooks.", flush=True)
    else:
        print(f"{total} celdas malformadas. Corre sin --revisar para arreglarlas.",
              flush=True)
        print("  Sin arreglar, los notebooks fallan con SyntaxError en Colab y en\n"
              "  nbconvert, aunque se vean bien en VS Code.", flush=True)
    return total


def main() -> int:
    escribir = "--revisar" not in sys.argv
    limpiar = "--limpiar" in sys.argv
    malas = ejecutar(escribir, limpiar)
    # Con --revisar devuelve 1 si hay problemas: sirve para un hook o para CI.
    return 1 if (malas and not escribir) else 0


if __name__ == "__main__":
    sys.exit(main())
