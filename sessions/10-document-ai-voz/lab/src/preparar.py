"""preparar.py — donde se gana la pelea.

Convierte hojas de PDF en imagenes listas para OCR. Tres pasos, en este orden:

    1. Rasterizar la hoja completa con pypdfium2 al dpi_fisico de config.yaml.
    2. Partir la hoja en dos paginas logicas (este PDF viene a dos por hoja).
    3. Corregir la orientacion (este PDF viene rotado).

El orden no es negociable. Partir despues del OCR no sirve: el modelo ya mezclo las
dos paginas.

    Analogia para clase: es la diferencia entre darle al lector un libro abierto y
    derecho, o darle una fotocopia doble, chueca y al reves. El lector es el mismo. El
    resultado no.

Por que rasterizar y no extraer las imagenes embebidas: el PDF no guarda una foto de
la hoja, guarda el rompecabezas desarmado. Si pides "las imagenes", te dan las piezas
sueltas (9 a 63 por hoja). Hay que pedir la foto del rompecabezas armado, que es lo
que hace el renderizador.

Uso:
    python -m src.preparar              # todas las hojas
    python -m src.preparar 3            # solo la hoja fisica 3
    python -m src.preparar 1 5          # hojas 1 a 5
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from src.comun import cargar_config, configurar_logging, preparar_directorios, ruta_absoluta

log = configurar_logging("preparar")


def numero_pagina_logica(hoja: int, posicion: int, orden_mitades: str) -> int:
    """Numero de pagina logica a partir de la hoja fisica y la mitad.

    `posicion` es 0 para la mitad superior y 1 para la inferior.

    Verificado sobre el documento real: la mitad INFERIOR es la pagina de numero
    menor. El orden de lectura es inferior, luego superior. Si se invierte, el informe
    sale con los parrafos desordenados y nadie se da cuenta hasta que es tarde.
    """
    if orden_mitades == "inferior_primero":
        indice_en_hoja = 0 if posicion == 1 else 1
    else:
        indice_en_hoja = posicion
    return (hoja - 1) * 2 + indice_en_hoja + 1


def nombre_salida(hoja: int, pagina_logica: int) -> str:
    """Nombre de archivo que preserva el orden logico de lectura.

    El formato h057_p114.png ordena bien alfabeticamente, que es como lo van a leer
    tanto el sistema de archivos como el estudiante.
    """
    return f"h{hoja:03d}_p{pagina_logica:03d}.png"


def rasterizar_hoja(ruta_pdf: Path, hoja: int, dpi: int):
    """Renderiza una hoja fisica completa a un bitmap PIL al DPI indicado.

    pypdfium2 es pip puro: no exige Poppler como pdf2image, ni arrastra la licencia
    AGPL de PyMuPDF. Un estudiante puede reutilizar este codigo sin sorpresas.
    """
    import pypdfium2 as pdfium

    documento = pdfium.PdfDocument(str(ruta_pdf))
    try:
        pagina = documento[hoja - 1]
        # pypdfium2 trabaja con escala, no con DPI: 72 puntos por pulgada es la base.
        escala = dpi / 72
        bitmap = pagina.render(scale=escala)
        return bitmap.to_pil()
    finally:
        documento.close()


def partir_en_mitades(imagen, eje_corte: str) -> list:
    """Parte la hoja por la mitad del eje indicado.

    Devuelve [mitad_superior, mitad_inferior] para el corte horizontal, que es el caso
    de este documento: las dos paginas estan una sobre otra.
    """
    ancho, alto = imagen.size
    if eje_corte == "horizontal":
        medio = alto // 2
        return [
            imagen.crop((0, 0, ancho, medio)),
            imagen.crop((0, medio, ancho, alto)),
        ]
    medio = ancho // 2
    return [
        imagen.crop((0, 0, medio, alto)),
        imagen.crop((medio, 0, ancho, alto)),
    ]


def corregir_orientacion(imagen, rotacion: int | str):
    """Rota la imagen el angulo fijado en config.yaml.

    Con `rotacion: auto` no se rota aqui: se delega al clasificador de orientacion de
    PaddleOCR, que se activa en ocr_run.py. Con un valor fijo se rota ahora, antes del
    OCR, que es mas rapido y mas predecible.

    Verificado sobre el documento real: el angulo correcto es 270, no 90. Con 90 la
    pagina sale cabeza abajo.
    """
    if rotacion == "auto" or rotacion == 0:
        return imagen
    # PIL rota en sentido ANTIHORARIO. El valor de config.yaml se interpreta igual,
    # asi que 270 significa 270 grados antihorarios. Verificado a ojo sobre la hoja 1:
    # con 270 la caratula queda derecha; con 90 sale cabeza abajo.
    # expand=True para que la imagen rotada no quede recortada a la caja original.
    return imagen.rotate(int(rotacion), expand=True)


def preparar_hoja(
    ruta_pdf: Path,
    hoja: int,
    config: dict[str, Any],
    destino: Path,
    forzar: bool = False,
) -> list[Path]:
    """Prepara una hoja fisica y devuelve las rutas de las imagenes generadas.

    No recomputa lo que ya existe en disco: correr dos veces seguidas no vuelve a
    rasterizar. Para rehacer una hoja, pasar forzar=True o borrar el PNG.
    """
    render = config["render"]
    dpi = render["dpi_fisico"]
    dos_por_pagina = render["dos_por_pagina"]
    orden = render.get("orden_mitades", "inferior_primero")

    # Se calculan primero los nombres de salida para poder saltar la hoja completa
    # sin pagar el costo de rasterizarla.
    if dos_por_pagina:
        esperados = [
            destino / nombre_salida(hoja, numero_pagina_logica(hoja, posicion, orden))
            for posicion in (0, 1)
        ]
    else:
        esperados = [destino / nombre_salida(hoja, hoja)]

    if not forzar and all(p.exists() for p in esperados):
        log.info("Hoja %d: ya preparada, se omite (%s)", hoja,
                 ", ".join(p.name for p in esperados))
        return esperados

    log.info("Hoja %d: rasterizando a %d DPI", hoja, dpi)
    hoja_completa = rasterizar_hoja(ruta_pdf, hoja, dpi)
    log.info("Hoja %d: bitmap de %dx%d px", hoja, *hoja_completa.size)

    if dos_por_pagina:
        mitades = partir_en_mitades(hoja_completa, render["eje_corte"])
    else:
        mitades = [hoja_completa]

    generadas: list[Path] = []
    for posicion, mitad in enumerate(mitades):
        pagina_logica = (
            numero_pagina_logica(hoja, posicion, orden) if dos_por_pagina else hoja
        )
        derecha = corregir_orientacion(mitad, render["rotacion"])

        salida = destino / nombre_salida(hoja, pagina_logica)
        salida.parent.mkdir(parents=True, exist_ok=True)
        # Guardado incremental: cada mitad se escribe apenas termina. Un proceso de 57
        # hojas que se corta en la 55 no puede perder las 54 anteriores.
        derecha.save(salida)
        generadas.append(salida)
        log.info("Hoja %d, pagina logica %d -> %s (%dx%d px)",
                 hoja, pagina_logica, salida.name, *derecha.size)

    return generadas


def ejecutar(
    hoja_inicial: int = 1,
    hoja_final: int | None = None,
    config: dict[str, Any] | None = None,
    forzar: bool = False,
) -> list[Path]:
    """Prepara un rango de hojas fisicas. Sin argumentos, prepara el PDF completo."""
    config = config or cargar_config()
    preparar_directorios(config)

    ruta_pdf = ruta_absoluta(config["rutas"]["pdf_entrada"])
    if not ruta_pdf.exists():
        raise FileNotFoundError(f"No existe el PDF de entrada: {ruta_pdf}")

    destino = ruta_absoluta(config["rutas"]["procesados"])

    import pypdfium2 as pdfium
    documento = pdfium.PdfDocument(str(ruta_pdf))
    total_hojas = len(documento)
    documento.close()

    hoja_final = hoja_final or total_hojas
    hoja_final = min(hoja_final, total_hojas)

    render = config["render"]
    log.info("=== preparar.py ===")
    log.info("Hojas %d a %d de %d. DPI fisico %d, dos_por_pagina=%s, rotacion=%s",
             hoja_inicial, hoja_final, total_hojas, render["dpi_fisico"],
             render["dos_por_pagina"], render["rotacion"])
    if render["dos_por_pagina"]:
        log.info("Orden de mitades: %s (verificado: la inferior es la pagina menor)",
                 render.get("orden_mitades", "inferior_primero"))

    todas: list[Path] = []
    for hoja in range(hoja_inicial, hoja_final + 1):
        todas.extend(preparar_hoja(ruta_pdf, hoja, config, destino, forzar=forzar))
        log.info("Progreso: hoja %d/%d lista", hoja, hoja_final)

    print("\n" + "=" * 78)
    print("PREPARACION")
    print("=" * 78)
    print(f"{len(todas)} imagenes listas para OCR en {destino}", flush=True)
    print(f"DPI fisico {render['dpi_fisico']} -> la pagina logica queda cerca de "
          f"{int(render['dpi_fisico'] * 0.707)} DPI efectivos", flush=True)
    print("=" * 78)

    return todas


def main() -> int:
    argumentos = [int(a) for a in sys.argv[1:3]]
    if len(argumentos) == 0:
        ejecutar()
    elif len(argumentos) == 1:
        ejecutar(argumentos[0], argumentos[0])
    else:
        ejecutar(argumentos[0], argumentos[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
