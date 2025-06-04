import re
from pathlib import Path
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as plt

# Define los rangos de mosaicos que cubren Perú
valid_h = {str(i).zfill(2) for i in range(9, 13)}   # h09, h10, h11, h12
valid_v = {str(i).zfill(2) for i in range(8, 12)}   # v08, v09, v10, v11

# Ruta a la carpeta con los tif
folder = Path(r"C:\Users\usuario\Documents\GitHub\Spatial_Analysis_of_Peru-s_Protected_Areas\241878_hw4\modis_data\tifs")

# Filtrar archivos que cruzan Perú
peru_tiles = []
for tif_path in folder.glob("*.tif"):
    match = re.search(r"h(\d{2})v(\d{2})", tif_path.name)
    if match:
        h, v = match.groups()
        if h in valid_h and v in valid_v:
            peru_tiles.append(tif_path)

print(f"Archivos .tif que cruzan Perú encontrados: {len(peru_tiles)}")

# Abrir los archivos y guardarlos en una lista
src_files_to_mosaic = []
for tif_file in peru_tiles:
    src = rasterio.open(tif_file)
    src_files_to_mosaic.append(src)

# Crear el mosaico
mosaic, out_trans = merge(src_files_to_mosaic)

# Metadata para guardar el mosaico
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans
})

# Guardar mosaico en disco (opcional)
out_mosaic_path = folder / "mosaico_peru.tif"
with rasterio.open(out_mosaic_path, "w", **out_meta) as dest:
    dest.write(mosaic)

print(f"Mosaico guardado en: {out_mosaic_path}")

# Mostrar el mosaico (opcional)
plt.imshow(mosaic[0], cmap='viridis')
plt.title("Mosaico de cobertura arbórea para Perú")
plt.colorbar()
plt.show()

# Cerrar todos los archivos abiertos
for src in src_files_to_mosaic:
    src.close()
