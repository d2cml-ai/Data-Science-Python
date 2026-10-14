"""ensayo.py — ensayo cronometrado de la clase.

Corre los comandos que el profesor ejecuta en vivo y mide cuanto tarda cada uno,
contra el presupuesto de minutos que `GUION_CLASE_110MIN.md` les asigna.

No es parte del pipeline. Es la herramienta del paso T-2 del runbook: "ensayo completo
cronometrado, porque siempre sobra o falta 20 minutos".

Lo que mide es el **tiempo de maquina**, no el de clase. El tiempo de clase incluye
explicar, responder preguntas y recorrer el salon. La regla practica: si el tiempo de
maquina se come mas de la mitad del bloque, el bloque no entra.

Uso:
    python -m src.ensayo              # ensayo completo, desde cero
    python -m src.ensayo --con-cache  # sin borrar lo ya procesado
    python -m src.ensayo --cpu        # simula el carril B, sin GPU

Lo que este ensayo NO mide, y es donde esta el riesgo real del salon:

    - La instalacion. En el carril A son unos 3 minutos de Colab por estudiante, y
      25 a la vez contra el wifi del aula es otra cosa.
    - La primera descarga de los pesos del modelo. Aqui ya estaban en disco.
    - El tiempo humano: explicar, responder, recorrer el salon.
"""

from __future__ import annotations

import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.comun import cargar_config, configurar_logging, preparar_directorios, preparar_paddle, ruta_absoluta

log = configurar_logging("ensayo")


@dataclass
class Bloque:
    """Un bloque de la clase y lo que cuesta en tiempo de maquina."""

    numero: str
    nombre: str
    presupuesto_min: int
    comando: str
    segundos: float = 0.0
    error: str = ""

    @property
    def minutos(self) -> float:
        return self.segundos / 60

    @property
    def porcentaje(self) -> float:
        """Que parte del bloque se come la maquina."""
        return self.minutos / self.presupuesto_min * 100 if self.presupuesto_min else 0

    @property
    def veredicto(self) -> str:
        if self.error:
            return "FALLA"
        if self.porcentaje > 50:
            return "NO ENTRA"
        if self.porcentaje > 30:
            return "JUSTO"
        return "ok"


def _cronometrar(bloque: Bloque, funcion: Callable[[], Any]) -> Bloque:
    """Corre una funcion y guarda cuanto tardo."""
    log.info("--- Bloque %s: %s (presupuesto %d min) ---",
             bloque.numero, bloque.nombre, bloque.presupuesto_min)
    inicio = time.perf_counter()
    try:
        funcion()
    except Exception as e:  # noqa: BLE001 - un bloque que revienta no corta el ensayo
        bloque.error = str(e)[:120]
        log.error("Bloque %s fallo: %s", bloque.numero, e)
    bloque.segundos = time.perf_counter() - inicio
    log.info("Bloque %s: %.1f s (%.0f%% del presupuesto) -> %s",
             bloque.numero, bloque.segundos, bloque.porcentaje, bloque.veredicto)
    return bloque


def limpiar_estado(config: dict[str, Any]) -> None:
    """Borra lo procesado para medir desde cero, como en el salon.

    NO toca data/raw: ese es el original. Tampoco borra los pesos del modelo, porque
    el runbook exige tenerlos descargados antes de la clase; descargarlos en vivo
    nunca fue parte del plan.
    """
    for clave in ("procesados", "salidas"):
        ruta = ruta_absoluta(config["rutas"][clave])
        if ruta.exists():
            shutil.rmtree(ruta)
            log.info("Borrado %s", ruta)
    preparar_directorios(config)


def ejecutar(config: dict[str, Any] | None = None, limpiar: bool = True,
             forzar_cpu: bool = False) -> list[Bloque]:
    """Corre el ensayo completo y devuelve los bloques medidos."""
    config = config or cargar_config()
    preparar_directorios(config)

    if limpiar:
        log.info("Ensayo desde cero: se borra lo ya procesado.")
        limpiar_estado(config)
    else:
        log.info("Ensayo con cache: se reutiliza lo ya procesado.")

    # El carril de clase: nivel tiny, que es el unico que entra en el tiempo si
    # alguien corre en CPU. Ver GUION_CLASE_110MIN.md, bloque 4.
    ocr_clase = {**config["ocr"], "nivel": "tiny"}
    if forzar_cpu:
        # Simula el carril B: una maquina sin GPU. El benchmark igual mide las dos
        # condiciones, porque la comparacion es justamente lo que se ensena.
        ocr_clase["device"] = "cpu"
        log.warning("Ensayo del carril B: se fuerza device=cpu.")
    config_clase = {**config, "ocr": ocr_clase}

    from src import bench, extraer, ocr_run, preparar, triaje
    from src import doctor as mod_doctor

    bloques: list[Bloque] = []

    bloques.append(_cronometrar(
        Bloque("2", "doctor: verificar GPU", 18, "python -m src.doctor"),
        lambda: mod_doctor.diagnosticar(config_clase),
    ))

    bloques.append(_cronometrar(
        Bloque("1", "triaje: 57 hojas", 10, "python -m src.triaje"),
        lambda: triaje.ejecutar(config_clase),
    ))

    bloques.append(_cronometrar(
        Bloque("5a", "preparar: hojas 1-2", 6, "python -m src.preparar 1 2"),
        lambda: preparar.ejecutar(1, 2, config_clase),
    ))

    bloques.append(_cronometrar(
        Bloque("3", "primer OCR: 1 pagina", 15, "python -m src.ocr_run <una>"),
        lambda: ocr_run.ocr_imagen(
            ruta_absoluta(config["rutas"]["procesados"]) / "h001_p001.png",
            config_clase,
            ocr_run.construir_ocr(config_clase),
        ),
    ))

    bloques.append(_cronometrar(
        Bloque("4", "bench rapido: cpu vs gpu", 20, "python -m src.bench rapido"),
        lambda: bench.ejecutar(config_clase, rapido=True),
    ))

    bloques.append(_cronometrar(
        Bloque("5b", "OCR de las 4 mitades", 5, "python -m src.ocr_run"),
        lambda: ocr_run.ocr_lote(
            sorted(ruta_absoluta(config["rutas"]["procesados"]).glob("h00[12]_p*.png")),
            config_clase,
        ),
    ))

    bloques.append(_cronometrar(
        Bloque("5c", "extraer: 4 campos", 8, "python -m src.extraer"),
        lambda: extraer.ejecutar(config_clase, solo_reglas=True),
    ))

    imprimir_informe(bloques)
    return bloques


def imprimir_informe(bloques: list[Bloque]) -> None:
    """La tabla que decide si la clase entra en 110 minutos."""
    print("\n" + "=" * 92)
    print("ENSAYO CRONOMETRADO — tiempo de maquina por bloque")
    print("=" * 92)
    print(f"{'blq':<5} {'que corre':<28} {'presup':>7} {'maquina':>9} "
          f"{'% del bloque':>13} {'veredicto':>10}")
    print("-" * 92)

    total_maquina = 0.0
    total_presupuesto = 0
    for b in sorted(bloques, key=lambda x: x.numero):
        total_maquina += b.minutos
        total_presupuesto += b.presupuesto_min
        detalle = f" ({b.error})" if b.error else ""
        print(f"{b.numero:<5} {b.nombre:<28} {b.presupuesto_min:>5} m "
              f"{b.minutos:>7.1f} m {b.porcentaje:>12.0f}% {b.veredicto:>10}{detalle}",
              flush=True)

    print("-" * 92)
    print(f"{'':<5} {'TOTAL':<28} {total_presupuesto:>5} m "
          f"{total_maquina:>7.1f} m {total_maquina/total_presupuesto*100:>12.0f}%")
    print("=" * 92)

    holgura = total_presupuesto - total_maquina
    print(f"\nTiempo de maquina: {total_maquina:.1f} min de los {total_presupuesto} "
          f"presupuestados.")
    print(f"Queda para explicar, preguntas y recorrer el salon: {holgura:.1f} min.")

    problemas = [b for b in bloques if b.veredicto in ("NO ENTRA", "FALLA")]
    if problemas:
        print("\nBloques que no entran como estan:")
        for b in problemas:
            print(f"  - Bloque {b.numero} ({b.nombre}): {b.minutos:.1f} min de "
                  f"maquina sobre {b.presupuesto_min} de presupuesto.")
        print("\n  Cortes disponibles, en orden: bajar ocr.nivel a tiny, bajar\n"
              "  render.dpi_fisico, o reducir benchmark.paginas_medidas.")
    else:
        print("\nTodos los bloques entran. El cuello de botella siempre es el "
              "bloque 4.")

    print("\nRecordatorio: esto mide la maquina, no la clase. El guion asigna esos\n"
          "minutos a explicar ADEMAS de correr. Si la maquina se come mas de la\n"
          "mitad del bloque, el bloque no entra.", flush=True)


def main() -> int:
    preparar_paddle()
    limpiar = "--con-cache" not in sys.argv
    forzar_cpu = "--cpu" in sys.argv
    ejecutar(limpiar=limpiar, forzar_cpu=forzar_cpu)
    return 0


if __name__ == "__main__":
    sys.exit(main())
