import os
import json
import requests

# URL base del directorio en LAADS DAAC
SOURCE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD44B/2024/065"

# Ruta local donde se guardarán los archivos
DESTINATION_DIR = r"C:\Users\usuario\Documents\GitHub\Spatial_Analysis_of_Peru-s_Protected_Areas\241878_hw4\modis_data"

# Token actualizado (NO LO COMPARTAS públicamente)
TOKEN = "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImRhZm5lZGFmMTgiLCJleHAiOjE3NTMzOTU1NzksImlhdCI6MTc0ODIxMTU3OSwiaXNzIjoiaHR0cHM6Ly91cnMuZWFydGhkYXRhLm5hc2EuZ292IiwiaWRlbnRpdHlfcHJvdmlkZXIiOiJlZGxfb3BzIiwiYWNyIjoiZWRsIiwiYXNzdXJhbmNlX2xldmVsIjozfQ.bfreu9sZJ0IFI6Nh6b-H6vNgGbeLjQyhyURrZhhLtA8puXT1xtOO6SJpPciwN1Hcio79cFwG4N_Vrn1J5Ke8gFs3Hs4JMJX_jF3R30c2DhY3KeszXjyLjZnvKPKcw-jrn3TUVkKAfUxMC5rBIENIqNJywFQUWHVGX4ROF7-rNqQFcPS8pYK-bD9t_VKmNnl-2-N3Wpb3sD1K_hSXCwOrELpur7YInzgeizuixumSu-1f7br86tDPqcrFJMycg23LxLNXEOnTAEVgnafcVI3hujExiGAJV4Hgpi1-6WCNGlPC7SyrZOVk-BTX1hfSyekcYEFc1P_uy5V3lYGWaxbjdg"

# Encabezado con autenticación
HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

def get_file_list():
    """Obtiene la lista de archivos disponibles en el servidor"""
    print("📦 Obteniendo lista de archivos disponibles...")
    response = requests.get(SOURCE_URL + ".json", headers=HEADERS)
    response.raise_for_status()
    return response.json()["content"]

def download_file(filename):
    """Descarga un archivo individual si no existe"""
    url = f"{SOURCE_URL}/{filename}"
    local_path = os.path.join(DESTINATION_DIR, filename)
    if os.path.exists(local_path):
        print(f"✅ Ya existe, se omite: {filename}")
        return
    print(f"⬇️  Descargando: {filename}")
    with requests.get(url, headers=HEADERS, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    """Función principal"""
    os.makedirs(DESTINATION_DIR, exist_ok=True)
    file_list = get_file_list()
    for file in file_list:
        if int(file["size"]) == 0:
            continue  # ignora archivos vacíos
        download_file(file["name"])

if __name__ == "__main__":
    try:
        main()
        print("\n✅ Descarga completada correctamente.")
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")

