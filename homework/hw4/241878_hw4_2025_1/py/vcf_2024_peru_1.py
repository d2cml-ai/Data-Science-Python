import re
from pathlib import Path
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as plt

# 🔧 NUEVO rango que incluye Tumbes y todo Perú sin exceso
valid_h = {'09', '10', '11'}
valid_v = {'08', '09', '10'}

# Ruta a la carpeta con los tif
folder = Path(r"C:\Users\usuario\Documents\GitHub\Spatial_Analysis_of_Peru-s_Protected_Areas\241878_hw4\modis_data\tifs")

# Filtrar solo los mosaicos necesarios
peru_tiles = []
for tif_path in folder.glob("*.tif"):
    match = re.search(r"h(\d{2})v(\d{2})", tif_path.name)
    if match:
        h, v = match.groups()
        if h in valid_h and v in valid_v:
            peru_tiles.append(tif_path)

print(f"Archivos .tif que cubren Perú encontrados: {len(peru_tiles)}")

# Abrir los archivos seleccionados
src_files_to_mosaic = [rasterio.open(tif) for tif in peru_tiles]

# Crear mosaico
mosaic, out_trans = merge(src_files_to_mosaic)

# Guardar nueva metadata
out_meta = src_files_to_mosaic[0].meta.copy()
out_meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_trans
})

# Guardar en disco
out_mosaic_path = folder / "mosaico_peru_completo.tif"
with rasterio.open(out_mosaic_path, "w", **out_meta) as dest:
    dest.write(mosaic)

print(f"✅ Mosaico completo guardado en: {out_mosaic_path}")

# Mostrar imagen
plt.figure(figsize=(10, 10))
plt.imshow(mosaic[0], cmap='viridis')
plt.title("Mosaico completo de Perú (incluye Tumbes)")
plt.colorbar(label="Cobertura arbórea")
plt.axis('off')
plt.show()

# Cerrar archivos
for src in src_files_to_mosaic:
    src.close()


