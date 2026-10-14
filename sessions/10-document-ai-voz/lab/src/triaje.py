"""triaje.py — la regla de oro.

Clasifica cada hoja del PDF en `texto` o `imagen` y produce un reporte.

    Regla de oro: usar OCR SOLO en las paginas que son imagen. En el resto, extraccion
    directa, que es gratis e instantanea.

    Analogia para clase: el triaje es la enfermera que decide quien pasa a emergencia.
    No todos los pacientes necesitan cirugia. El OCR es la cirugia: cara y lenta. Solo
    se opera a quien lo necesita.

Uso:
    python -m src.triaje
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_directorios, ruta_absoluta

log = configurar_logging("triaje")


@dataclass
class FilaTriaje:
    """Una hoja fisica del PDF, ya clasificada."""

    pagina: int
    caracteres: int
    imagenes_embebidas: int
    clase: str


def contar_paginas_imagen(filas: list[FilaTriaje]) -> int:
    """Cuantas hojas quedaron clasificadas como imagen y por tanto necesitan OCR."""
    return sum(1 for f in filas if f.clase == "imagen")


def clasificar_pdf(ruta_pdf: Path, umbral_caracteres: int) -> list[FilaTriaje]:
    """Recorre el PDF hoja por hoja y clasifica cada una.

    Una hoja es `texto` si su capa de texto supera el umbral de caracteres. Si no,
    es `imagen` y necesita OCR.

    Se cuentan tambien las imagenes embebidas porque son el dato que delata un escaneo
    en mosaico: este documento tiene entre 9 y 63 por hoja, lo que explica por que hay
    que rasterizar la pagina completa en vez de extraer sus imagenes.
    """
    from pypdf import PdfReader

    lector = PdfReader(str(ruta_pdf))
    total = len(lector.pages)
    log.info("PDF abierto: %s, %d hojas fisicas", ruta_pdf.name, total)

    filas: list[FilaTriaje] = []
    for indice, pagina in enumerate(lector.pages, start=1):
        try:
            texto = pagina.extract_text() or ""
        except Exception as e:  # noqa: BLE001 - una hoja corrupta no debe cortar el triaje
            log.warning("Hoja %d: no se pudo extraer texto (%s). Se asume imagen.", indice, e)
            texto = ""

        caracteres = len(texto.strip())

        try:
            n_imagenes = len(pagina.images)
        except Exception:  # noqa: BLE001
            n_imagenes = 0

        clase = "texto" if caracteres > umbral_caracteres else "imagen"
        filas.append(FilaTriaje(indice, caracteres, n_imagenes, clase))

        # Progreso cada 10 hojas: un proceso silencioso es un proceso roto.
        if indice % 10 == 0 or indice == total:
            log.info("Triaje %d/%d hojas revisadas", indice, total)

    return filas


def escribir_csv(filas: list[FilaTriaje], destino: Path) -> None:
    """Guarda el reporte de triaje. Cada fila se escribe apenas se tiene."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(
            f, fieldnames=["pagina", "caracteres", "imagenes_embebidas", "clase"]
        )
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(asdict(fila))
            f.flush()
    log.info("Reporte escrito en %s", destino)


def resumir(filas: list[FilaTriaje]) -> str:
    """Una linea de resumen, la que se lee en voz alta en clase."""
    total = len(filas)
    con_imagen = contar_paginas_imagen(filas)
    con_texto = total - con_imagen
    porcentaje = (con_imagen / total * 100) if total else 0.0
    return (
        f"{total} paginas: {con_texto} con texto, {con_imagen} imagen "
        f"-> {porcentaje:.0f}% requiere OCR"
    )


def ejecutar(config: dict[str, Any] | None = None) -> list[FilaTriaje]:
    """Corre el triaje completo sobre el PDF de config.yaml."""
    config = config or cargar_config()
    preparar_directorios(config)

    ruta_pdf = ruta_absoluta(config["rutas"]["pdf_entrada"])
    if not ruta_pdf.exists():
        raise FileNotFoundError(
            f"No existe el PDF de entrada: {ruta_pdf}\n"
            "Copialo a data/raw/ o cambia rutas.pdf_entrada en config.yaml."
        )

    umbral = config["triaje"]["umbral_caracteres"]
    log.info("Umbral de clasificacion: mas de %d caracteres = texto", umbral)

    filas = clasificar_pdf(ruta_pdf, umbral)

    destino = ruta_absoluta(config["rutas"]["salidas"]) / "triaje.csv"
    escribir_csv(filas, destino)

    rango_imagenes = (
        f"{min(f.imagenes_embebidas for f in filas)} a "
        f"{max(f.imagenes_embebidas for f in filas)}"
    ) if filas else "0"

    resumen = resumir(filas)
    print("\n" + "=" * 78)
    print("TRIAJE")
    print("=" * 78)
    print(resumen, flush=True)
    print(f"Imagenes embebidas por hoja: {rango_imagenes}", flush=True)
    print(
        "  Ese rango es la prueba de que el escaner guardo cada hoja partida en\n"
        "  mosaicos. Por eso se rasteriza la pagina completa y no se extraen sus\n"
        "  imagenes: extraerlas devuelve decenas de fragmentos inservibles.",
        flush=True,
    )
    print(f"Detalle por hoja: {destino}", flush=True)
    print("=" * 78)
    log.info(resumen)

    return filas


def main() -> int:
    ejecutar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
