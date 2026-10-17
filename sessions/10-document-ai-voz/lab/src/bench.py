"""bench.py — medir sin autoenganarse.

    Analogia para clase: cronometrar cuanto tarda tu mama en servir la sopa, pero
    arrancar el cronometro cuando todavia esta prendiendo la cocina. El primer plato
    siempre parece lentisimo. La primera inferencia incluye cargar el modelo a la VRAM
    e inicializar CUDA.

Protocolo obligatorio:

    1. Descartar las primeras paginas_calentamiento paginas.
    2. Medir paginas_medidas paginas, el mismo conjunto en todas las condiciones.
    3. Reportar MEDIANA de segundos por pagina, no promedio: un pico aislado no debe
       mover la conclusion.
    4. Muestrear VRAM en un hilo aparte y reportar el pico menos la linea base.
    5. Reportar tambien CALIDAD, no solo velocidad. Una configuracion que acelera y
       empeora la transcripcion no es una mejora.

Advertencia operativa: cerrar el navegador antes de medir. Ocupa VRAM y compite por
el GPU. Una medicion con el navegador abierto no es comparable con otra sin el.

Uso:
    python -m src.bench                 # matriz completa de config.yaml
    python -m src.bench rapido          # solo cpu vs gpu al DPI por defecto
"""

from __future__ import annotations

import csv
import statistics
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_directorios, preparar_paddle, ruta_absoluta
from src.doctor import DELTA_VRAM_MINIMO_MIB, leer_vram_usada_mib

log = configurar_logging("bench")


@dataclass
class Condicion:
    """Una celda de la matriz device x dpi x nivel."""

    device: str
    dpi: int
    nivel: str

    def etiqueta(self) -> str:
        return f"{self.device}/{self.dpi}dpi/{self.nivel}"


@dataclass
class Medicion:
    """Resultado de medir una condicion completa."""

    device: str
    dpi: int
    nivel: str
    paginas_medidas: int
    mediana_seg_pagina: float
    minimo_seg: float
    maximo_seg: float
    vram_pico_delta_mib: float
    lineas_promedio: float
    confianza_promedio: float
    lineas_bajo_umbral_pct: float
    # Veredicto sobre donde corrio DE VERDAD, deducido del delta de VRAM medido
    # mientras se cargaba el modelo. Vale "gpu", "cpu" o "?" cuando el modelo ya
    # estaba en memoria de una condicion anterior y el delta no significa nada.
    #
    # No se usa paddle.device.get_device() para esto: ese valor es global y devuelve
    # gpu:0 aunque el objeto PaddleOCR se haya construido con device="cpu". Una
    # columna que miente es peor que no tener columna.
    veredicto: str = "?"
    error: str = ""


class VigilanteVRAM:
    """Muestrea la VRAM en un hilo aparte mientras corre la medicion.

    Se mide el delta sobre la linea base, nunca el absoluto: en esta maquina el
    navegador ya ocupa VRAM antes de que el modelo cargue.
    """

    def __init__(self, intervalo: float = 0.25) -> None:
        self.intervalo = intervalo
        self.base: float | None = None
        self.pico: float = 0.0
        self._corriendo = False
        self._hilo: threading.Thread | None = None

    def __enter__(self) -> VigilanteVRAM:
        self.base = leer_vram_usada_mib()
        self.pico = self.base or 0.0
        if self.base is None:
            log.info("Sin GPU NVIDIA: no se muestrea VRAM en esta corrida.")
            return self
        self._corriendo = True
        self._hilo = threading.Thread(target=self._muestrear, daemon=True)
        self._hilo.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=2)

    def _muestrear(self) -> None:
        while self._corriendo:
            medida = leer_vram_usada_mib()
            if medida is not None:
                self.pico = max(self.pico, medida)
            time.sleep(self.intervalo)

    @property
    def delta(self) -> float:
        """Pico menos linea base, en MiB. 0 si no hay GPU."""
        if self.base is None:
            return 0.0
        return self.pico - self.base


def _veredicto_vram(delta_mib: float, medible: bool) -> str:
    """Traduce el delta de VRAM en un veredicto sobre donde corrio el modelo.

    Solo es interpretable cuando el modelo se cargo dentro de esta medicion. Si venia
    de una condicion anterior, no se afirma nada: se devuelve "?".
    """
    if not medible:
        return "?"
    return "gpu" if delta_mib >= DELTA_VRAM_MINIMO_MIB else "cpu"


def construir_matriz(config: dict[str, Any], rapido: bool = False) -> list[Condicion]:
    """Arma la lista de condiciones a medir a partir de config.yaml."""
    cfg = config["benchmark"]

    if rapido:
        # El modo rapido es el de la clase: solo cpu vs gpu, en las condiciones reales.
        # Medido en esta maquina: CPU tarda unos 68 s por pagina y GPU unos 8. Con las
        # 10 paginas del protocolo completo el bloque 4 se comeria 15 minutos, asi que
        # el modo rapido mide menos paginas. Sigue descartando calentamiento y sigue
        # reportando la mediana: lo que se recorta es el tamano de la muestra, no el
        # protocolo.
        cfg["paginas_calentamiento"] = min(cfg["paginas_calentamiento"], 1)
        cfg["paginas_medidas"] = min(cfg["paginas_medidas"], 3)
        log.info("Modo rapido: %d pagina de calentamiento, %d medidas por condicion",
                 cfg["paginas_calentamiento"], cfg["paginas_medidas"])
        return [
            Condicion(device, config["render"]["dpi_fisico"], config["ocr"]["nivel"])
            for device in cfg["condiciones_device"]
        ]

    return [
        Condicion(device, dpi, nivel)
        for device in cfg["condiciones_device"]
        for dpi in cfg["condiciones_dpi"]
        for nivel in cfg["niveles"]
    ]


def imagenes_para_medir(config: dict[str, Any], dpi: int) -> list[Path]:
    """Prepara y devuelve el mismo conjunto de paginas para todas las condiciones.

    Que sea el MISMO conjunto es lo que hace comparables las mediciones. Si cada
    condicion midiera paginas distintas, la diferencia podria venir del contenido y no
    del dispositivo.
    """
    from src import preparar

    cfg = config["benchmark"]
    necesarias = cfg["paginas_calentamiento"] + cfg["paginas_medidas"]
    # Cada hoja fisica rinde dos paginas logicas cuando el PDF viene a dos por hoja.
    hojas = (necesarias + 1) // 2 if config["render"]["dos_por_pagina"] else necesarias

    # El DPI de la condicion manda sobre el de config.yaml, en una copia: no se muta
    # la configuracion global.
    config_dpi = {**config, "render": {**config["render"], "dpi_fisico": dpi}}
    procesados = ruta_absoluta(config["rutas"]["procesados"]) / f"bench_{dpi}dpi"

    rutas: list[Path] = []
    ruta_pdf = ruta_absoluta(config["rutas"]["pdf_entrada"])
    for hoja in range(1, hojas + 1):
        rutas.extend(
            preparar.preparar_hoja(ruta_pdf, hoja, config_dpi, procesados)
        )

    return sorted(rutas)[:necesarias]


def medir_condicion(condicion: Condicion, config: dict[str, Any]) -> Medicion:
    """Mide una condicion siguiendo el protocolo completo."""
    from src import ocr_run

    cfg = config["benchmark"]
    n_calentamiento = cfg["paginas_calentamiento"]
    n_medidas = cfg["paginas_medidas"]
    umbral = config["ocr"]["umbral_confianza"]

    log.info("--- Condicion %s ---", condicion.etiqueta())

    try:
        rutas = imagenes_para_medir(config, condicion.dpi)
    except Exception as e:  # noqa: BLE001
        log.error("Condicion %s: no se pudieron preparar las imagenes: %s",
                  condicion.etiqueta(), e)
        return Medicion(condicion.device, condicion.dpi, condicion.nivel,
                        0, 0, 0, 0, 0, 0, 0, 0, error=str(e))

    # El vigilante arranca ANTES de construir el modelo. Si arrancara despues del
    # calentamiento, la linea base ya incluiria el modelo cargado y el delta daria
    # cero, lo que parece un fallback mudo sin serlo.
    tiempos: list[float] = []
    lineas_por_pagina: list[int] = []
    confianzas: list[float] = []
    bajo_umbral = 0
    total_lineas = 0

    # Si el modelo ya estaba construido de una condicion anterior, el delta de VRAM
    # de esta medicion no dice nada sobre donde corre.
    vram_medible = not ocr_run.modelo_en_cache(config, condicion.device,
                                               condicion.nivel)
    if not vram_medible:
        log.info("Condicion %s: el modelo ya estaba cargado, el delta de VRAM de esta "
                 "condicion no es interpretable", condicion.etiqueta())

    with VigilanteVRAM() as vigilante:
        try:
            ocr = ocr_run.construir_ocr(config, device=condicion.device,
                                        nivel=condicion.nivel)
        except Exception as e:  # noqa: BLE001
            log.error("Condicion %s: no se pudo construir el modelo: %s",
                      condicion.etiqueta(), e)
            return Medicion(condicion.device, condicion.dpi, condicion.nivel,
                            0, 0, 0, 0, 0, 0, 0, 0, error=str(e))

        # Paso 1: calentamiento. Estas paginas se corren y se descartan.
        log.info("Calentamiento: %d paginas que NO se miden (cargan el modelo a la "
                 "VRAM e inicializan CUDA)", n_calentamiento)
        for ruta in rutas[:n_calentamiento]:
            try:
                ocr.predict(str(ruta))
            except Exception as e:  # noqa: BLE001
                log.warning("Calentamiento fallo en %s: %s", ruta.name, e)

        # Paso 2 a 5: medicion, con registro de calidad ademas de velocidad.
        a_medir = rutas[n_calentamiento:n_calentamiento + n_medidas]
        log.info("Midiendo %d paginas", len(a_medir))

        for indice, ruta in enumerate(a_medir, start=1):
            t0 = time.perf_counter()
            try:
                resultado = ocr.predict(str(ruta))
            except Exception as e:  # noqa: BLE001
                log.error("Fallo la inferencia en %s: %s", ruta.name, e)
                continue
            tiempos.append(time.perf_counter() - t0)

            lineas = ocr_run._normalizar_resultado(resultado)
            lineas_por_pagina.append(len(lineas))
            total_lineas += len(lineas)
            for linea in lineas:
                confianzas.append(linea.confianza)
                if linea.confianza < umbral:
                    bajo_umbral += 1

            log.info("  %s %d/%d: %.2f s, %d lineas",
                     condicion.etiqueta(), indice, len(a_medir),
                     tiempos[-1], len(lineas))

    if not tiempos:
        return Medicion(condicion.device, condicion.dpi, condicion.nivel,
                        0, 0, 0, 0, vigilante.delta, 0, 0, 0,
                        veredicto=_veredicto_vram(vigilante.delta, vram_medible),
                        error="ninguna pagina se pudo medir")

    medicion = Medicion(
        device=condicion.device,
        dpi=condicion.dpi,
        nivel=condicion.nivel,
        paginas_medidas=len(tiempos),
        mediana_seg_pagina=round(statistics.median(tiempos), 3),
        minimo_seg=round(min(tiempos), 3),
        maximo_seg=round(max(tiempos), 3),
        vram_pico_delta_mib=round(vigilante.delta, 1),
        lineas_promedio=round(statistics.mean(lineas_por_pagina), 1),
        confianza_promedio=round(statistics.mean(confianzas), 4) if confianzas else 0.0,
        lineas_bajo_umbral_pct=round(bajo_umbral / total_lineas * 100, 1)
        if total_lineas else 0.0,
        veredicto=_veredicto_vram(vigilante.delta, vram_medible),
    )

    log.info("Condicion %s: mediana %.2f s/pagina, VRAM delta %+.0f MiB, "
             "veredicto %s, confianza %.3f",
             condicion.etiqueta(), medicion.mediana_seg_pagina,
             medicion.vram_pico_delta_mib, medicion.veredicto,
             medicion.confianza_promedio)

    return medicion


def escribir_csv(mediciones: list[Medicion], destino: Path) -> None:
    """Guarda la tabla del benchmark. Cada fila se escribe apenas se tiene."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    campos = list(asdict(mediciones[0]).keys()) if mediciones else []
    with open(destino, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for m in mediciones:
            escritor.writerow(asdict(m))
            f.flush()
    log.info("Tabla escrita en %s", destino)


def imprimir_tabla(mediciones: list[Medicion]) -> None:
    """Imprime la tabla que se proyecta en clase."""
    print("\n" + "=" * 100)
    print("BENCHMARK")
    print("=" * 100)
    cabecera = (f"{'pedido':<7} {'corrio':<7} {'dpi':>5} {'nivel':<7} {'med s/pag':>10} "
                f"{'min':>7} {'max':>7} {'VRAM d':>8} {'lineas':>7} "
                f"{'confianza':>10} {'<umbral %':>10}")
    print(cabecera)
    print("-" * 100)
    for m in mediciones:
        if m.error:
            print(f"{m.device:<7} {m.veredicto:<7} {m.dpi:>5} {m.nivel:<7} "
                  f"FALLA: {m.error[:52]}")
            continue
        print(f"{m.device:<7} {m.veredicto:<7} {m.dpi:>5} {m.nivel:<7} "
              f"{m.mediana_seg_pagina:>10.2f} "
              f"{m.minimo_seg:>7.2f} {m.maximo_seg:>7.2f} "
              f"{m.vram_pico_delta_mib:>8.0f} {m.lineas_promedio:>7.1f} "
              f"{m.confianza_promedio:>10.3f} {m.lineas_bajo_umbral_pct:>10.1f}",
              flush=True)
    print("=" * 100)

    # La lectura de la tabla, en el orden en que hay que mirarla.
    validas = [m for m in mediciones if not m.error and m.mediana_seg_pagina > 0]
    por_device: dict[str, list[Medicion]] = {}
    for m in validas:
        por_device.setdefault(m.device, []).append(m)

    if "cpu" in por_device and "gpu" in por_device:
        mejor_cpu = min(por_device["cpu"], key=lambda m: m.mediana_seg_pagina)
        mejor_gpu = min(por_device["gpu"], key=lambda m: m.mediana_seg_pagina)
        factor = mejor_cpu.mediana_seg_pagina / mejor_gpu.mediana_seg_pagina
        print(f"\nMejor CPU: {mejor_cpu.mediana_seg_pagina:.2f} s/pagina "
              f"({mejor_cpu.nivel}, {mejor_cpu.dpi} dpi)")
        print(f"Mejor GPU: {mejor_gpu.mediana_seg_pagina:.2f} s/pagina "
              f"({mejor_gpu.nivel}, {mejor_gpu.dpi} dpi)")
        print(f"Factor de aceleracion: {factor:.1f}x", flush=True)
        print("  Honestidad obligatoria: parte de ese factor es GPU buena y parte es\n"
              "  CPU mal configurada. Un CPU con inferencia optimizada acorta la\n"
              "  brecha. Prometer 40x sin matices es vender humo.", flush=True)

    # El fallback mudo se detecta por la VRAM que ocupo CARGAR el modelo, medida
    # dentro de la propia condicion. Si el modelo venia cargado de una condicion
    # anterior el veredicto es "?" y no se afirma nada.
    mudas = [m for m in validas if m.device == "gpu" and m.veredicto == "cpu"]
    if mudas:
        print("\nATENCION: se pidio device=gpu y la VRAM no se movio al cargar el "
              "modelo.\n"
              "  Eso es el fallback mudo: corre python -m src.doctor", flush=True)

    primera_gpu = next((m for m in validas if m.device == "gpu"), None)
    if primera_gpu is not None and primera_gpu.vram_pico_delta_mib > 0:
        print(f"\nVRAM que ocupo cargar el modelo: "
              f"{primera_gpu.vram_pico_delta_mib:+.0f} MiB sobre la linea base.")
        print("  En las condiciones siguientes el delta sale cero porque el modelo ya\n"
              "  estaba en la tarjeta; esas filas llevan '?' en la columna 'corrio',\n"
              "  que es la forma honesta de decir que ahi no se midio nada.",
              flush=True)


def ejecutar(config: dict[str, Any] | None = None, rapido: bool = False) -> list[Medicion]:
    """Corre la matriz completa del benchmark."""
    config = config or cargar_config()
    preparar_directorios(config)

    matriz = construir_matriz(config, rapido=rapido)
    log.info("=== bench.py: %d condiciones ===", len(matriz))
    log.info("Protocolo: %d paginas de calentamiento descartadas, %d medidas, "
             "se reporta la MEDIANA",
             config["benchmark"]["paginas_calentamiento"],
             config["benchmark"]["paginas_medidas"])
    log.warning("Cierra el navegador antes de medir: ocupa VRAM y compite por el GPU.")

    destino = ruta_absoluta(config["rutas"]["salidas"]) / "benchmark.csv"

    mediciones: list[Medicion] = []
    for indice, condicion in enumerate(matriz, start=1):
        log.info("Condicion %d/%d", indice, len(matriz))
        mediciones.append(medir_condicion(condicion, config))
        # Guardado incremental: si la condicion 7 de 18 revienta, las 6 anteriores
        # ya estan en disco.
        escribir_csv(mediciones, destino)

    imprimir_tabla(mediciones)
    print(f"\nTabla completa: {destino}", flush=True)

    return mediciones


def main() -> int:
    preparar_paddle()
    rapido = len(sys.argv) > 1 and sys.argv[1] == "rapido"
    ejecutar(rapido=rapido)
    return 0


if __name__ == "__main__":
    sys.exit(main())
