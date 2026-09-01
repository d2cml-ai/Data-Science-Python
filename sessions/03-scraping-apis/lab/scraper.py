"""
scraper.py — Web Scraper de Resultados de Admision UNMSM 2026-II

Utiliza Selenium para navegar la pagina de resultados del examen de admision
de la Universidad Nacional Mayor de San Marcos, extrae los datos de TODOS los
postulantes de TODAS las carreras y los consolida en un archivo Excel.
"""

# ============================================================
# IMPORTACIONES
# ============================================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time
from datetime import datetime


# ============================================================
# CONSTANTES
# ============================================================
URL_PRINCIPAL = "https://admision.unmsm.edu.pe/Website20262/A/A.html"
DIRECTORIO_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
ARCHIVO_EXCEL = os.path.join(DIRECTORIO_OUTPUT, "resultados_sanmarcos.xlsx")


# ============================================================
# FUNCIONES
# ============================================================

def crear_driver():
    """
    Configura e inicializa el navegador Chrome en modo headless.
    Headless significa que el navegador corre sin interfaz grafica,
    ideal para scraping automatizado en servidores o scripts.

    Returns:
        webdriver.Chrome: Instancia del navegador configurada.
    """
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--window-size=1920,1080")
    opciones.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=opciones)
    driver.set_page_load_timeout(30)
    return driver


def obtener_enlaces_carreras(driver):
    """
    Navega a la pagina principal y recolecta los enlaces de todas las carreras.
    Cada carrera tiene un link con patron: {codigo}/results.html

    Args:
        driver: Instancia de Selenium WebDriver.

    Returns:
        list[dict]: Lista con 'nombre' y 'url' de cada carrera.
    """
    driver.get(URL_PRINCIPAL)

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a[href*='results.html']")
        )
    )

    elementos = driver.find_elements(By.CSS_SELECTOR, "a[href*='results.html']")

    carreras = []
    for elem in elementos:
        href = elem.get_attribute("href")
        nombre = elem.text.strip()
        if href and nombre:
            carreras.append({"nombre": nombre, "url": href})

    return carreras


def extraer_postulantes_de_carrera(driver, url):
    """
    Accede a la pagina de resultados de UNA carrera y extrae TODOS los postulantes.

    Estrategia clave:
      - La tabla usa DataTables con paginacion visual de 50 registros.
      - Sin embargo, TODOS los datos estan cargados en el DOM (client-side).
      - Usamos la API JavaScript de DataTables — table.rows().every() —
        para iterar TODOS los registros sin importar la paginacion.
      - Los nombres estan codificados en Base64 (atributo data-auth de
        elementos con clase .obfuscated). El JavaScript de la propia pagina
        los decodifica al cargar, asi que cuando leemos innerText ya estan
        decodificados.

    Args:
        driver: Instancia de Selenium WebDriver.
        url:    URL de la pagina de resultados de la carrera.

    Returns:
        list[dict]: Lista de diccionarios, uno por postulante.
    """
    driver.get(url)

    # Esperar a que la tabla exista en el DOM
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "tablaPostulantes"))
    )

    # Esperar a que jQuery + DataTables esten completamente inicializados
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script(
            "return (typeof jQuery !== 'undefined' && "
            "jQuery.fn.DataTable.isDataTable('#tablaPostulantes'))"
        )
    )

    # Breve pausa para que el JS decodifique los nombres Base64
    time.sleep(0.5)

    # Extraer TODOS los registros via la API de DataTables (ignora paginacion).
    #
    # Estructura real de cada fila (verificada con inspeccion del DOM):
    #   celdas[0] = Codigo         -> innerText
    #   celdas[1] = Nombre         -> innerText (ya decodificado de Base64 por el JS de la pagina)
    #   celdas[2] = Escuela        -> innerText (idem)
    #   celdas[3] = Puntaje        -> atributo data-score en el propio <td> (texto plano, NO Base64)
    #   celdas[4] = Merito E.P     -> atributo data-merit en el propio <td> (texto plano, NO Base64)
    #   celdas[5] = Observacion    -> innerText
    #
    # El innerText de celdas[3] y celdas[4] esta VACIO; el valor real esta
    # en los atributos data-score y data-merit del <td>.
    postulantes = driver.execute_script("""
        var tabla = $('#tablaPostulantes').DataTable();
        var resultado = [];

        tabla.rows().every(function() {
            var fila = this.node();
            var celdas = fila.querySelectorAll('td');

            if (celdas.length >= 6) {
                resultado.push({
                    codigo:      celdas[0].innerText.trim(),
                    nombre:      celdas[1].innerText.trim(),
                    escuela:     celdas[2].innerText.trim(),
                    puntaje:     celdas[3].getAttribute('data-score') || '',
                    merito:      celdas[4].getAttribute('data-merit') || '',
                    observacion: celdas[5].innerText.trim()
                });
            }
        });

        return resultado;
    """)

    return postulantes if postulantes else []


def exportar_a_excel(datos, archivo):
    """
    Convierte la lista de datos a un DataFrame de pandas y exporta a Excel.

    Args:
        datos:   Lista de diccionarios con los datos de postulantes.
        archivo: Ruta completa del archivo .xlsx de salida.

    Returns:
        pd.DataFrame: El DataFrame resultante.
    """
    df = pd.DataFrame(datos)

    df = df.rename(columns={
        "carrera":     "Carrera",
        "codigo":      "Codigo",
        "nombre":      "Apellidos y Nombres",
        "escuela":     "Escuela",
        "puntaje":     "Puntaje",
        "merito":      "Merito E.P",
        "observacion": "Observacion"
    })

    columnas_orden = [
        "Carrera", "Codigo", "Apellidos y Nombres",
        "Escuela", "Puntaje", "Merito E.P", "Observacion"
    ]
    df = df[columnas_orden]

    df.to_excel(archivo, index=False, sheet_name="Resultados", engine="openpyxl")

    return df


# ============================================================
# EJECUCION PRINCIPAL
# ============================================================

def main():
    """Funcion principal que orquesta todo el proceso de scraping."""

    print("=" * 65)
    print("  SCRAPER - Resultados Admision UNMSM 2026-II")
    print("=" * 65)
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  URL:    {URL_PRINCIPAL}")
    print("=" * 65)

    # Crear directorio de salida si no existe
    os.makedirs(DIRECTORIO_OUTPUT, exist_ok=True)

    # Iniciar navegador
    print("\n[1/3] Iniciando navegador Chrome (headless)...")
    driver = crear_driver()
    print("       Navegador listo.\n")

    todos_los_datos = []
    errores = []

    try:
        # ---- PASO 1: Obtener enlaces de carreras ----
        print("[2/3] Obteniendo lista de carreras...")
        carreras = obtener_enlaces_carreras(driver)
        print(f"       -> {len(carreras)} carreras encontradas.\n")

        # ---- PASO 2: Iterar cada carrera y extraer postulantes ----
        print(f"[3/3] Extrayendo postulantes de cada carrera:\n")

        for i, carrera in enumerate(carreras, 1):
            try:
                postulantes = extraer_postulantes_de_carrera(driver, carrera["url"])

                for p in postulantes:
                    p["carrera"] = carrera["nombre"]

                todos_los_datos.extend(postulantes)

                print(
                    f"  [{i:3d}/{len(carreras)}] {carrera['nombre']}"
                    f" -- {len(postulantes)} postulantes"
                )

            except Exception as e:
                errores.append(carrera["nombre"])
                print(
                    f"  [{i:3d}/{len(carreras)}] ERROR en {carrera['nombre']}: {e}"
                )

        # ---- PASO 3: Exportar a Excel ----
        print("\n" + "-" * 65)

        if todos_los_datos:
            print(f"\nExportando {len(todos_los_datos)} registros a Excel...")
            df = exportar_a_excel(todos_los_datos, ARCHIVO_EXCEL)
            print(f"Archivo guardado: {ARCHIVO_EXCEL}")

            # Resumen final
            print(f"\n{'=' * 65}")
            print(f"  RESUMEN FINAL")
            print(f"{'=' * 65}")
            print(f"  Carreras procesadas:  {len(carreras) - len(errores)}/{len(carreras)}")
            print(f"  Carreras con error:   {len(errores)}")
            if errores:
                for e in errores:
                    print(f"    - {e}")
            print(f"  Total postulantes:    {len(todos_los_datos)}")
            print(f"  Archivo Excel:        {ARCHIVO_EXCEL}")
            print(f"  Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 65}")
        else:
            print("\nNo se extrajeron datos. Verifica la conexion y la URL.")

    finally:
        driver.quit()
        print("\nNavegador cerrado. Proceso terminado.")


if __name__ == "__main__":
    main()
