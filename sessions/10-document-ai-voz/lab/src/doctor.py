"""doctor.py — el semaforo de GPU.

No hace OCR. Responde una sola pregunta: la GPU esta realmente disponible y en uso?

Existe porque PaddlePaddle no lanza error cuando la GPU falla: cae a CPU en silencio
y sigue funcionando. El usuario cree que tiene aceleracion y no la tiene.

    Analogia para clase: tienes bicicleta y auto. Le dices al chofer "llevame". Si la
    llave del auto no esta colgada, no te avisa: te lleva en bicicleta. Llegas tarde y
    nunca te enteras de que existia el auto.

Uso:
    python -m src.doctor
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from importlib import metadata
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_paddle

log = configurar_logging("doctor")

# Cargar el modelo a la VRAM mueve varios cientos de MiB. Por debajo de este delta,
# el modelo no esta en la GPU aunque se haya pedido.
DELTA_VRAM_MINIMO_MIB = 200


@dataclass
class Chequeo:
    """Resultado de un chequeo individual del semaforo."""

    numero: int
    nombre: str
    ok: bool
    detalle: str

    def linea(self) -> str:
        estado = "OK   " if self.ok else "FALLA"
        return f"[{self.numero}/6] {estado} | {self.nombre:<26} | {self.detalle}"


# --------------------------------------------------------------------------- #
# Lectura de nvidia-smi
# --------------------------------------------------------------------------- #

def _ejecutar_nvidia_smi(consulta: str) -> str | None:
    """Ejecuta nvidia-smi con una consulta. Devuelve None si no hay driver."""
    try:
        salida = subprocess.run(
            ["nvidia-smi", f"--query-gpu={consulta}", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if salida.returncode != 0:
        return None
    return salida.stdout.strip()


def leer_vram_usada_mib() -> float | None:
    """VRAM ocupada en este instante, en MiB. None si no hay GPU NVIDIA."""
    salida = _ejecutar_nvidia_smi("memory.used")
    if not salida:
        return None
    try:
        return float(salida.splitlines()[0].strip())
    except (ValueError, IndexError):
        return None


def chequeo_1_driver() -> Chequeo:
    """Driver NVIDIA presente y version legible."""
    salida = _ejecutar_nvidia_smi("name,driver_version")
    if not salida:
        return Chequeo(
            1, "Driver NVIDIA", False,
            "nvidia-smi no responde: no hay GPU NVIDIA o falta el driver. Modo CPU.",
        )
    partes = [c.strip() for c in salida.splitlines()[0].split(",")]
    nombre, driver = partes[0], partes[1]
    return Chequeo(1, "Driver NVIDIA", True, f"{nombre}, driver {driver}")


# --------------------------------------------------------------------------- #
# Wheels de Paddle
# --------------------------------------------------------------------------- #

def paquetes_paddle_instalados() -> list[str]:
    """Nombres de los wheels de paddlepaddle instalados en este entorno."""
    encontrados = []
    for nombre in ("paddlepaddle", "paddlepaddle-gpu"):
        try:
            metadata.version(nombre)
            encontrados.append(nombre)
        except metadata.PackageNotFoundError:
            continue
    return encontrados


def chequeo_2_wheel_unico() -> Chequeo:
    """Debe existir exactamente un wheel de Paddle.

    Tener paddlepaddle y paddlepaddle-gpu a la vez no produce ningun error: todo corre
    en CPU 40 veces mas lento sin avisar. Es la falla numero 1 del laboratorio.
    """
    instalados = paquetes_paddle_instalados()

    if not instalados:
        return Chequeo(
            2, "Wheel unico de Paddle", False,
            "no hay ningun paddlepaddle instalado. Ver PLAN_60MIN.md paso 2.",
        )

    if len(instalados) > 1:
        log.error(
            "ABORTA: estan instalados los dos wheels de Paddle %s. Conviven sin error "
            "y el resultado es que todo corre en CPU 40 veces mas lento sin avisar.",
            instalados,
        )
        raise SystemExit(
            "\nFALLA DURA: paddlepaddle y paddlepaddle-gpu instalados a la vez.\n"
            "Desinstala el wheel de CPU y vuelve a correr el doctor:\n"
            "    python -m pip uninstall -y paddlepaddle\n"
        )

    unico = instalados[0]
    detalle = f"solo {unico}=={metadata.version(unico)}"
    if unico == "paddlepaddle":
        detalle += " (wheel de CPU: no habra aceleracion por GPU)"
    return Chequeo(2, "Wheel unico de Paddle", True, detalle)


# --------------------------------------------------------------------------- #
# Chequeos que preguntan a Paddle
# --------------------------------------------------------------------------- #

def chequeo_3_compilacion_cuda() -> Chequeo:
    """paddle.is_compiled_with_cuda(): el wheel trae soporte CUDA compilado."""
    try:
        import paddle
    except ImportError as e:
        return Chequeo(3, "Compilacion CUDA", False, f"no se pudo importar paddle: {e}")

    if bool(paddle.is_compiled_with_cuda()):
        return Chequeo(3, "Compilacion CUDA", True, "is_compiled_with_cuda() = True")
    return Chequeo(
        3, "Compilacion CUDA", False,
        "is_compiled_with_cuda() = False: este wheel es de CPU. Modo CPU.",
    )


def chequeo_4_dispositivo_activo() -> Chequeo:
    """paddle.device.get_device(): que dispositivo usara Paddle por defecto."""
    try:
        import paddle
    except ImportError as e:
        return Chequeo(4, "Dispositivo activo", False, f"no se pudo importar paddle: {e}")

    dispositivo = paddle.device.get_device()
    if dispositivo.startswith("gpu"):
        return Chequeo(4, "Dispositivo activo", True, f"get_device() = {dispositivo}")
    return Chequeo(
        4, "Dispositivo activo", False,
        f"get_device() = {dispositivo}: Paddle usara CPU. Modo CPU.",
    )


def chequeo_5_run_check() -> Chequeo:
    """paddle.utils.run_check(): la verificacion que trae el propio framework."""
    import contextlib
    import io

    try:
        import paddle
    except ImportError as e:
        return Chequeo(5, "Verificacion de Paddle", False,
                       f"no se pudo importar paddle: {e}")

    capturado = io.StringIO()
    try:
        with contextlib.redirect_stdout(capturado), contextlib.redirect_stderr(capturado):
            paddle.utils.run_check()
    except Exception as e:  # noqa: BLE001 - run_check falla de muchas formas distintas
        return Chequeo(5, "Verificacion de Paddle", False, f"run_check() lanzo: {e}")

    texto = capturado.getvalue()
    log.debug("Salida de run_check(): %s", texto.replace("\n", " | "))
    if "PaddlePaddle is installed successfully" in texto:
        encontrado = re.search(r"(\d+)\s+GPU", texto)
        extra = f", {encontrado.group(1)} GPU detectada(s)" if encontrado else ""
        return Chequeo(5, "Verificacion de Paddle", True,
                       f"run_check() exitoso{extra}")
    return Chequeo(
        5, "Verificacion de Paddle", False,
        "run_check() no confirmo instalacion exitosa. Ver logs/doctor.log",
    )


# --------------------------------------------------------------------------- #
# Chequeo 6: el unico que no se puede falsificar
# --------------------------------------------------------------------------- #

def chequeo_6_prueba_real(config: dict[str, Any]) -> Chequeo:
    """Inferencia OCR real, midiendo si la VRAM se mueve.

    Los cinco chequeos anteriores pueden dar verde y aun asi el objeto PaddleOCR
    correr en CPU, porque falta el parametro device. Este es el unico que prueba algo:
    carga el modelo, hace una inferencia y compara la VRAM contra la linea base.

    La linea base no es cero: el navegador ya ocupa VRAM en esta maquina. Se mide el
    delta, nunca el absoluto.
    """
    device = config["ocr"]["device"]

    base = leer_vram_usada_mib()
    if base is None:
        return Chequeo(
            6, "Prueba real de inferencia", False,
            "sin GPU NVIDIA: no se puede medir VRAM. El OCR correra en CPU.",
        )
    log.info("Linea base de VRAM antes de cargar el modelo: %.0f MiB", base)

    try:
        import numpy as np
        from paddleocr import PaddleOCR
    except ImportError as e:
        return Chequeo(
            6, "Prueba real de inferencia", False,
            f"falta una dependencia ({e}). Ver PLAN_60MIN.md paso 4.",
        )

    log.info("Construyendo PaddleOCR con device=%r (el parametro de 3.x, nunca use_gpu)",
             device)
    t0 = time.perf_counter()
    try:
        ocr = PaddleOCR(lang=config["ocr"]["idioma"], device=device)
    except Exception as e:  # noqa: BLE001
        return Chequeo(6, "Prueba real de inferencia", False,
                       f"PaddleOCR no se pudo construir: {e}")

    # Imagen sintetica: no interesa el texto reconocido, interesa que el modelo corra.
    imagen = np.full((320, 960, 3), 255, dtype=np.uint8)
    imagen[140:180, 60:900] = 0

    pico = base
    try:
        ocr.predict(imagen)
        medida = leer_vram_usada_mib()
        if medida is not None:
            pico = max(pico, medida)
    except Exception as e:  # noqa: BLE001
        return Chequeo(6, "Prueba real de inferencia", False, f"la inferencia lanzo: {e}")

    transcurrido = time.perf_counter() - t0
    delta = pico - base
    log.info("Inferencia completada en %.1f s. VRAM pico %.0f MiB, delta %+.0f MiB",
             transcurrido, pico, delta)

    if delta >= DELTA_VRAM_MINIMO_MIB:
        return Chequeo(
            6, "Prueba real de inferencia", True,
            f"VRAM subio {delta:+.0f} MiB sobre la linea base: el modelo esta en GPU "
            f"({transcurrido:.1f} s)",
        )

    if device == "cpu":
        return Chequeo(
            6, "Prueba real de inferencia", True,
            f"corrio en CPU como pide config.yaml, VRAM plana ({transcurrido:.1f} s)",
        )

    return Chequeo(
        6, "Prueba real de inferencia", False,
        f"se pidio device={device!r} pero la VRAM solo movio {delta:+.0f} MiB: el "
        "modelo corre en CPU. Este es el fallback mudo.",
    )


# --------------------------------------------------------------------------- #
# Orquestacion
# --------------------------------------------------------------------------- #

def diagnosticar(config: dict[str, Any] | None = None) -> list[Chequeo]:
    """Corre los seis chequeos y devuelve la lista de resultados."""
    config = config or cargar_config()
    return [
        chequeo_1_driver(),
        chequeo_2_wheel_unico(),
        chequeo_3_compilacion_cuda(),
        chequeo_4_dispositivo_activo(),
        chequeo_5_run_check(),
        chequeo_6_prueba_real(config),
    ]


def hay_gpu_utilizable(config: dict[str, Any] | None = None) -> bool:
    """Atajo para los notebooks: True si la GPU quedo verificada de verdad."""
    chequeos = diagnosticar(config)
    return chequeos[3].ok and chequeos[5].ok


def main() -> int:
    preparar_paddle()
    config = cargar_config()
    log.info("=== doctor.py, semaforo de GPU ===")
    log.info("config.yaml pide ocr.device=%r, ocr.nivel=%r",
             config["ocr"]["device"], config["ocr"]["nivel"])

    chequeos = diagnosticar(config)

    print("\n" + "=" * 100)
    print("SEMAFORO DE GPU")
    print("=" * 100)
    for c in chequeos:
        print(c.linea(), flush=True)
        log.info(c.linea())
    print("=" * 100)

    if chequeos[3].ok and chequeos[5].ok:
        print("MODO DISPONIBLE: GPU. El OCR corre acelerado.", flush=True)
        log.info("Modo disponible: GPU")
    else:
        print(
            "MODO DISPONIBLE: CPU. El pipeline funciona igual, pero mas lento.\n"
            "  Para que la clase no se eternice, pon ocr.nivel: tiny en config.yaml.",
            flush=True,
        )
        log.warning("Modo disponible: CPU. Se degrada, y se dice en voz alta.")

    # Termina con codigo 0 incluso sin GPU: no tener GPU no es un error del programa.
    return 0


if __name__ == "__main__":
    sys.exit(main())
