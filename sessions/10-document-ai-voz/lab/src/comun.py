"""Utilidades compartidas: carga de configuracion y logging.

Este modulo no hace trabajo propio. Existe para que ningun otro modulo tenga que
repetir como se lee `config.yaml` ni como se configura el log.

Regla del repositorio: todo valor ajustable sale de `config.yaml`. Si un modulo
necesita un numero, lo pide aqui.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# Raiz del proyecto: este archivo vive en <raiz>/src/comun.py
RAIZ = Path(__file__).resolve().parent.parent


def cargar_entorno() -> bool:
    """Carga las variables de `.env` al entorno del proceso. Devuelve si lo encontro.

    Existe para que NINGUN notebook ni modulo tenga que escribir una clave de API en
    su propio texto. Se llama sola al importar este modulo, asi que basta con tener
    el `.env` en la raiz del proyecto.

    Por que importa: una clave escrita en una celda se guarda dentro del .ipynb, el
    .ipynb se commitea, y una clave que llego a un repositorio publico queda en el
    historial de git para siempre. Borrarla despues no la saca del historial; hay que
    revocarla. La plantilla esta en `.env.example`, y `.gitignore` excluye el `.env`.
    """
    ruta = RAIZ / ".env"
    if not ruta.exists():
        return False
    try:
        from dotenv import load_dotenv
    except ImportError:
        # Sin python-dotenv se lee a mano: no vale la pena fallar por esto.
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))
        return True
    load_dotenv(ruta)
    return True


# Se carga al importar: cualquier `from src.x import y` deja el entorno listo.
cargar_entorno()


def cargar_config(ruta: str | Path | None = None) -> dict[str, Any]:
    """Devuelve el contenido de config.yaml como diccionario."""
    ruta = Path(ruta) if ruta else RAIZ / "config.yaml"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe {ruta}. Este archivo es obligatorio: todos los parametros "
            "del pipeline salen de ahi."
        )
    with open(ruta, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ruta_absoluta(valor: str | Path) -> Path:
    """Convierte una ruta de config.yaml (relativa a la raiz) en ruta absoluta."""
    p = Path(valor)
    return p if p.is_absolute() else RAIZ / p


def configurar_logging(nombre: str, config: dict[str, Any] | None = None) -> logging.Logger:
    """Configura logging a consola y a archivo, sin buffer.

    El archivo de log importa mas que la consola: cuando otro programa captura la
    salida estandar, Python la bufferiza y el progreso no se ve nunca. Por eso cada
    modulo escribe tambien a `logs/<nombre>.log` con flush inmediato.
    """
    config = config or cargar_config()
    dir_logs = ruta_absoluta(config["rutas"]["logs"])
    dir_logs.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(nombre)
    if logger.handlers:  # ya configurado; importar dos veces no debe duplicar lineas
        return logger

    logger.setLevel(logging.INFO)
    # PaddleX instala sus propios handlers en el logger raiz. Sin esto, cada linea
    # nuestra sale tres veces y la salida se vuelve ilegible en clase.
    logger.propagate = False
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Consola: stdout con flush inmediato en cada registro.
    consola = logging.StreamHandler(sys.stdout)
    consola.setFormatter(formato)
    consola.flush = sys.stdout.flush  # type: ignore[method-assign]
    logger.addHandler(consola)

    # Archivo: se reabre en cada emision para que el progreso sea legible en vivo.
    archivo = _HandlerSinBuffer(dir_logs / f"{nombre}.log")
    archivo.setFormatter(formato)
    logger.addHandler(archivo)

    return logger


class _HandlerSinBuffer(logging.FileHandler):
    """FileHandler que hace flush despues de cada linea.

    Un proceso de 40 paginas que escribe su progreso a un archivo bufferizado es un
    proceso silencioso. Este bug ya costo horas en el proyecto original.
    """

    def __init__(self, ruta: Path) -> None:
        super().__init__(ruta, mode="a", encoding="utf-8", delay=False)

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def preparar_directorios(config: dict[str, Any]) -> None:
    """Crea las carpetas de salida declaradas en config.yaml si no existen."""
    for clave in ("procesados", "salidas", "logs"):
        ruta_absoluta(config["rutas"][clave]).mkdir(parents=True, exist_ok=True)


def preparar_paddle() -> Path | None:
    """Deja listo el entorno de Paddle. Debe llamarse ANTES de importar paddle o paddleocr.

    1. CPU: apaga oneDNN (MKLDNN) por defecto. Con paddlepaddle 3.4.0, PaddleX lo activa en CPU
       y el modelo falla con 'ConvertPirAttribute2RuntimeAttribute not support'.
       Con la variable apagada, el OCR en CPU funciona. La GPU no usa oneDNN, no cambia.

    2. Windows: pone en el PATH las DLL de CUDA 13 que trae paddlepaddle-gpu 3.4.0.

    Las DLL (cublas64_13.dll, etc.) viven dentro del .venv, en nvidia/cu13/bin/x86_64,
    y Windows no las busca ahi. Sin este paso Paddle muere al importarse con
    'cublas64_13.dll ... error code 126'. Debe llamarse ANTES de importar paddle.

    No hace nada en Linux/Colab, ni si la carpeta no existe (entonces Paddle usa CPU).
    Devuelve la carpeta agregada, o None.
    """
    os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"

    if sys.platform != "win32":
        return None
    carpeta = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "cu13" / "bin" / "x86_64"
    if not carpeta.is_dir():
        return None
    os.environ["PATH"] = str(carpeta) + os.pathsep + os.environ.get("PATH", "")
    logging.getLogger("comun").info("DLL de CUDA 13 agregadas al PATH: %s", carpeta)
    return carpeta
