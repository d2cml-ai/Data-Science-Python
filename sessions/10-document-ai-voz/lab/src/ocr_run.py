"""ocr_run.py — la inferencia.

Envuelve PaddleOCR. Devuelve, por cada linea reconocida, tres datos que valen igual:

    texto      la cadena reconocida
    caja       cuatro puntos en la imagen: permite resaltar en el original lo que la
               IA afirma
    confianza  numero entre 0 y 1: permite decidir que revisa un humano

    Analogia para clase: no es un lector que te cuenta el libro. Es un lector que
    ademas te senala con el dedo en que parte de la pagina esta cada frase, y te dice
    que tan seguro esta de cada una.

Puntos no negociables de este modulo:

    - El objeto PaddleOCR se construye UNA sola vez y se reutiliza. Reconstruirlo por
      pagina recarga el modelo y arruina cualquier medicion.
    - El parametro es device. Nunca use_gpu, que es de PaddleOCR 2.x.
    - Al construirlo se registra en el log que dispositivo quedo activo, leido del
      propio Paddle. Lo que importa es donde corrio, no donde se pidio correr.

Uso:
    python -m src.ocr_run                          # todos los PNG de data/processed
    python -m src.ocr_run data/processed/h001_p002.png
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_directorios, preparar_paddle, ruta_absoluta

log = configurar_logging("ocr_run")

# Nombres de los modelos PP-OCRv6 por nivel. El compromiso tamano/precision es la
# leccion: tiny 1.5M parametros y 73.5% de precision; medium 34.5M y 83.2%.
MODELOS_POR_NIVEL = {
    "tiny": ("PP-OCRv5_mobile_det", "PP-OCRv5_mobile_rec"),
    "small": ("PP-OCRv5_mobile_det", "PP-OCRv5_server_rec"),
    "medium": ("PP-OCRv5_server_det", "PP-OCRv5_server_rec"),
}

# Instancia unica del modelo, cacheada por (nivel, device).
_INSTANCIAS: dict[tuple[str, str], Any] = {}


@dataclass
class LineaOCR:
    """Una linea reconocida: texto, geometria y confianza."""

    texto: str
    caja: list[list[float]]
    confianza: float


def modelo_en_cache(config: dict[str, Any], device: str | None = None,
                    nivel: str | None = None) -> bool:
    """True si ese (nivel, device) ya tiene un modelo construido en memoria.

    bench.py lo consulta antes de medir: si el modelo ya estaba cargado, el delta de
    VRAM de esa condicion no significa nada y no se debe interpretar.
    """
    cfg = config["ocr"]
    clave = (nivel or cfg["nivel"], device or cfg["device"])
    return clave in _INSTANCIAS


def construir_ocr(config: dict[str, Any], device: str | None = None,
                  nivel: str | None = None) -> Any:
    """Construye (o reutiliza) el objeto PaddleOCR.

    La cache por (nivel, device) existe porque bench.py recorre varias condiciones y
    no debe pagar la carga del modelo mas de una vez por condicion.
    """
    cfg = config["ocr"]
    device = device or cfg["device"]
    nivel = nivel or cfg["nivel"]

    clave = (nivel, device)
    if clave in _INSTANCIAS:
        return _INSTANCIAS[clave]

    from paddleocr import PaddleOCR

    log.info("Construyendo PaddleOCR: nivel=%s, device=%s, idioma=%s",
             nivel, device, cfg["idioma"])

    parametros: dict[str, Any] = {
        "device": device,
        "use_doc_orientation_classify": cfg["usar_clasificador_orientacion"],
        "use_doc_unwarping": cfg["usar_desenrollado"],
        "use_textline_orientation": cfg["usar_clasificador_orientacion"],
    }

    if device == "cpu":
        # Verificado el 13 de octubre de 2026 sobre paddlepaddle-gpu 3.3.0 en Windows:
        # forzar CPU con oneDNN activo revienta en cada inferencia con
        #     (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support
        # Es un bug del ejecutor PIR con oneDNN, no del documento ni del modelo.
        # Apagarlo deja el carril CPU funcionando, algo mas lento.
        parametros["enable_mkldnn"] = False
        log.info("CPU: se desactiva oneDNN (enable_mkldnn=False). Sin esto, este "
                 "wheel falla en cada inferencia sobre CPU en Windows.")

    det, rec = MODELOS_POR_NIVEL.get(nivel, (None, None))
    if det and rec:
        # Cuando se nombran los modelos explicitamente, `lang` se ignora: el modelo
        # ya determina el idioma. Pasarlo igual solo produce un UserWarning en cada
        # construccion, y un warning que siempre sale es un warning que nadie lee.
        parametros["text_detection_model_name"] = det
        parametros["text_recognition_model_name"] = rec
    else:
        parametros["lang"] = cfg["idioma"]

    t0 = time.perf_counter()
    ocr = PaddleOCR(**parametros)
    log.info("Modelo cargado en %.1f s", time.perf_counter() - t0)

    _registrar_dispositivo_real(device)

    _INSTANCIAS[clave] = ocr
    return ocr


def _registrar_dispositivo_real(device_pedido: str) -> None:
    """Deja en el log donde quedo Paddle de verdad, no donde se le pidio correr.

    Esta es la linea que delata el fallback mudo. Si se pidio gpu y Paddle dice cpu,
    el log lo grita; el silencio es el enemigo de este repositorio.
    """
    try:
        import paddle
        real = paddle.device.get_device()
    except Exception as e:  # noqa: BLE001
        log.warning("No se pudo leer el dispositivo real de Paddle: %s", e)
        return

    log.info("Dispositivo pedido: %s | dispositivo real segun Paddle: %s",
             device_pedido, real)
    if device_pedido == "gpu" and not real.startswith("gpu"):
        log.error(
            "ATENCION: se pidio GPU y Paddle reporta %s. Esto es el fallback mudo: "
            "todo va a funcionar, mucho mas lento, y nada va a avisar. "
            "Corre python -m src.doctor",
            real,
        )


def ocr_imagen(ruta_imagen: Path, config: dict[str, Any] | None = None,
               ocr: Any | None = None) -> list[LineaOCR]:
    """Corre OCR sobre una imagen y devuelve las lineas reconocidas."""
    config = config or cargar_config()
    ocr = ocr or construir_ocr(config)

    t0 = time.perf_counter()
    resultado = ocr.predict(str(ruta_imagen))
    transcurrido = time.perf_counter() - t0

    lineas = _normalizar_resultado(resultado)
    log.info("%s: %d lineas en %.2f s", ruta_imagen.name, len(lineas), transcurrido)
    return lineas


def _normalizar_resultado(resultado: Any) -> list[LineaOCR]:
    """Convierte la salida de PaddleOCR 3.x a una lista de LineaOCR.

    PaddleOCR 3.x devuelve una lista de diccionarios con las claves rec_texts,
    rec_scores y rec_polys. Se normaliza aqui para que el resto del pipeline no
    dependa de la forma exacta que devuelve la libreria.
    """
    lineas: list[LineaOCR] = []
    if not resultado:
        return lineas

    for bloque in resultado:
        datos = bloque.get("res", bloque) if isinstance(bloque, dict) else bloque
        textos = datos.get("rec_texts", []) or []
        puntajes = datos.get("rec_scores", []) or []
        cajas = datos.get("rec_polys", datos.get("dt_polys", [])) or []

        for indice, texto in enumerate(textos):
            confianza = float(puntajes[indice]) if indice < len(puntajes) else 0.0
            if indice < len(cajas):
                caja = [[float(x), float(y)] for x, y in cajas[indice]]
            else:
                caja = []
            lineas.append(LineaOCR(texto=str(texto), caja=caja, confianza=confianza))

    return lineas


def texto_plano(lineas: list[LineaOCR]) -> str:
    """Une las lineas en un solo texto, en el orden en que las devolvio el modelo."""
    return "\n".join(l.texto for l in lineas)


def guardar_resultado(ruta_imagen: Path, lineas: list[LineaOCR], destino: Path) -> Path:
    """Escribe el resultado de una pagina a disco apenas termina.

    Dos archivos por pagina: el JSON con texto, cajas y confianza, y un .txt con solo
    el texto, que es lo que el estudiante va a leer.
    """
    destino.mkdir(parents=True, exist_ok=True)
    base = ruta_imagen.stem

    ruta_json = destino / f"{base}.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump([asdict(l) for l in lineas], f, ensure_ascii=False, indent=1)
        f.flush()

    ruta_txt = destino / f"{base}.txt"
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(texto_plano(lineas))
        f.flush()

    return ruta_json


def ocr_lote(rutas: list[Path], config: dict[str, Any] | None = None,
             forzar: bool = False) -> dict[Path, list[LineaOCR]]:
    """Corre OCR sobre varias imagenes, reutilizando el modelo y cacheando en disco."""
    config = config or cargar_config()
    preparar_directorios(config)
    destino = ruta_absoluta(config["rutas"]["procesados"]) / "ocr"

    ocr = construir_ocr(config)
    umbral = config["ocr"]["umbral_confianza"]

    resultados: dict[Path, list[LineaOCR]] = {}
    total = len(rutas)
    for indice, ruta in enumerate(rutas, start=1):
        ruta_json = destino / f"{ruta.stem}.json"

        if not forzar and ruta_json.exists():
            with open(ruta_json, "r", encoding="utf-8") as f:
                crudo = json.load(f)
            resultados[ruta] = [LineaOCR(**d) for d in crudo]
            log.info("%s: ya procesada, se lee de cache (%d lineas)",
                     ruta.name, len(resultados[ruta]))
        else:
            lineas = ocr_imagen(ruta, config, ocr)
            guardar_resultado(ruta, lineas, destino)
            resultados[ruta] = lineas

            bajas = sum(1 for l in lineas if l.confianza < umbral)
            if bajas:
                log.warning("%s: %d de %d lineas por debajo de la confianza %.2f. "
                            "Son las que conviene que lea un humano.",
                            ruta.name, bajas, len(lineas), umbral)

        log.info("Progreso OCR: %d/%d paginas", indice, total)

    return resultados


def ejecutar(config: dict[str, Any] | None = None,
             rutas: list[Path] | None = None) -> dict[Path, list[LineaOCR]]:
    """Corre OCR sobre las imagenes de data/processed."""
    config = config or cargar_config()

    if rutas is None:
        procesados = ruta_absoluta(config["rutas"]["procesados"])
        rutas = sorted(procesados.glob("h*_p*.png"))

    if not rutas:
        raise FileNotFoundError(
            "No hay imagenes en data/processed. Corre primero: python -m src.preparar"
        )

    log.info("=== ocr_run.py: %d imagenes ===", len(rutas))
    resultados = ocr_lote(rutas, config)

    total_lineas = sum(len(v) for v in resultados.values())
    confianzas = [l.confianza for v in resultados.values() for l in v]
    media = sum(confianzas) / len(confianzas) if confianzas else 0.0

    print("\n" + "=" * 78)
    print("OCR")
    print("=" * 78)
    print(f"{len(resultados)} paginas, {total_lineas} lineas reconocidas", flush=True)
    print(f"Confianza promedio: {media:.3f}", flush=True)
    print(f"Resultados en {ruta_absoluta(config['rutas']['procesados']) / 'ocr'}",
          flush=True)
    print("=" * 78)

    return resultados


def main() -> int:
    preparar_paddle()
    config = cargar_config()
    if len(sys.argv) > 1:
        rutas = [Path(a) for a in sys.argv[1:]]
        resultados = ejecutar(config, rutas)
        # Con una sola imagen conviene ver el resultado completo en pantalla.
        if len(rutas) == 1:
            for linea in resultados[rutas[0]]:
                print(f"  {linea.confianza:.3f}  {linea.texto}", flush=True)
    else:
        ejecutar(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
