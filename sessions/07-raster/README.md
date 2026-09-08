# Sesión 07 · Datos raster

## Entorno

```bash
uv sync --group raster --group geo
uv run jupyter lab
```

## Contenido

### Clase

| Notebook | Enfoque |
|---|---|
| **`lecture/raster_aplicado.ipynb`** | **Recomendado.** Aplicado: luces nocturnas como proxy de actividad económica distrital, cruzadas con áreas mineras. Corre de punta a punta. |
| `lecture/GIS_v2.ipynb` | Versión anterior, orientada a conceptos (CRS, formatos, geowombat). Requiere instalar `geowombat` desde GitHub. |
| `lecture/GIS.ipynb`, `lecture/Tutorial.ipynb` | Material de apoyo. |

### Laboratorio

`lab/RASTER.ipynb` y `lab/RASTER_LAB.ipynb` — precipitación por distrito.

## De qué trata `raster_aplicado.ipynb`

Construye una medida de actividad económica distrital desde imágenes satelitales,
porque en el Perú no existe PBI a nivel de distrito.

1. Abrir el raster VIIRS de luces nocturnas (2021, ~1 km)
2. Detectar los problemas del dato: 27 % de `NaN`, 98 % de píxeles en cero
3. **Zonal statistics**: pasar de píxeles a una fila por distrito
4. Validar el ranking contra lo que sabemos del país
5. Cruzar con un segundo raster de áreas mineras
6. Estimar si los distritos mineros concentran más actividad

Resultados que produce al ejecutarse:

- Los distritos más luminosos por km² son San Borja, Surquillo, Lince y San Isidro
- Las áreas mineras detectadas corresponden a Antapaccay, Toquepala, Cuajone,
  Cerro Verde, Antamina, Yanacocha y Las Bambas
- Los distritos mineros tienen ~1.3 log-puntos más luminosidad total, robusto a
  controles por área, precipitación y efectos fijos de departamento (t = 8.2)

Conceptos que quedan: `nodata`, `all_touched`, `mean` frente a `sum`, y por qué
las áreas no se calculan en EPSG:4326.

## Datos

Se descargan desde Hugging Face; el notebook lo hace solo con `hf_hub_download`.

```bash
uv run python scripts/fetch_data.py 07-raster
```
