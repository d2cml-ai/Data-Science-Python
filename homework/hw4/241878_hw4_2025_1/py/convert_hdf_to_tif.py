import os
from osgeo import gdal
import sys

# Carpeta con los archivos .hdf descargados
INPUT_DIR = r"C:\Users\usuario\Documents\GitHub\Spatial_Analysis_of_Peru-s_Protected_Areas\241878_hw4\modis_data"

# Carpeta de salida para los .tif
OUTPUT_DIR = os.path.join(INPUT_DIR, "tifs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Términos posibles para buscar el subdataset de cobertura arbórea
TARGET_KEYWORDS = ["Percent_Tree_Cover", "Tree_Cover", "PCT_Tree_Cover", "tree", "cover"]

def list_subdatasets(hdf_file_path):
    """Lista todos los subdatasets disponibles en el archivo HDF"""
    print(f"\n📋 Subdatasets disponibles en {os.path.basename(hdf_file_path)}:")
    try:
        hdf_dataset = gdal.Open(hdf_file_path)
        if hdf_dataset is None:
            print("❌ Error: No se pudo abrir el archivo HDF")
            return []
        
        subdatasets = hdf_dataset.GetSubDatasets()
        for i, subdataset in enumerate(subdatasets):
            name, description = subdataset
            print(f"  {i+1}. {description}")
            print(f"     -> {name}")
        
        hdf_dataset = None  # Cerrar dataset
        return subdatasets
    except Exception as e:
        print(f"❌ Error al leer subdatasets: {e}")
        return []

def find_tree_cover_subdataset(subdatasets):
    """Busca el subdataset de cobertura arbórea"""
    for name, description in subdatasets:
        for keyword in TARGET_KEYWORDS:
            if keyword.lower() in description.lower() or keyword.lower() in name.lower():
                print(f"✅ Encontrado subdataset: {description}")
                return name, description
    return None, None

def convert_hdf_to_tif(hdf_file_path):
    print(f"\n🔍 Procesando: {os.path.basename(hdf_file_path)}")
    
    # Listar todos los subdatasets primero
    subdatasets = list_subdatasets(hdf_file_path)
    
    if not subdatasets:
        print("❌ No se encontraron subdatasets")
        return False
    
    # Buscar el subdataset de cobertura arbórea
    target_name, target_description = find_tree_cover_subdataset(subdatasets)
    
    if target_name is None:
        print("⚠️ No se encontró ningún subdataset relacionado con cobertura arbórea")
        print("💡 Usa el primer subdataset por defecto...")
        target_name, target_description = subdatasets[0]
    
    # Generar nombre de archivo de salida
    base_name = os.path.basename(hdf_file_path).replace(".hdf", "")
    output_name = f"{base_name}_TreeCover.tif"
    output_path = os.path.join(OUTPUT_DIR, output_name)
    
    try:
        print(f"🌀 Convirtiendo: {target_description}")
        print(f"📁 Guardando en: {output_name}")
        
        # Configurar opciones de traducción
        translate_options = gdal.TranslateOptions(
            format='GTiff',
            outputType=gdal.GDT_Float32,
            creationOptions=['COMPRESS=LZW', 'TILED=YES']
        )
        
        # Realizar la conversión
        result = gdal.Translate(output_path, target_name, options=translate_options)
        
        if result is None:
            print("❌ Error durante la conversión")
            return False
        
        result = None  # Cerrar dataset
        print(f"✅ Conversión exitosa: {output_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la conversión: {e}")
        return False

def main():
    print("🚀 Iniciando conversión de archivos HDF a GeoTIFF")
    print(f"📂 Directorio de entrada: {INPUT_DIR}")
    print(f"📂 Directorio de salida: {OUTPUT_DIR}")
    
    # Verificar que existe el directorio de entrada
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: El directorio {INPUT_DIR} no existe")
        return
    
    # Buscar archivos HDF
    hdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".hdf")]
    
    if not hdf_files:
        print(f"❌ No se encontraron archivos .hdf en {INPUT_DIR}")
        return
    
    print(f"📊 Encontrados {len(hdf_files)} archivos HDF")
    
    successful_conversions = 0
    for filename in hdf_files:
        hdf_path = os.path.join(INPUT_DIR, filename)
        if convert_hdf_to_tif(hdf_path):
            successful_conversions += 1
    
    print(f"\n🎉 Conversión completada!")
    print(f"✅ {successful_conversions}/{len(hdf_files)} archivos convertidos exitosamente")
    print(f"📁 Los archivos GeoTIFF están en: {OUTPUT_DIR}")

if __name__ == "__main__":
    # Configurar GDAL para mostrar errores
    gdal.UseExceptions()
    main()