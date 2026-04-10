import base64
import os
import re
import unicodedata
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from pyproj import Transformer

logger = logging.getLogger(__name__)

# --- Configuración de Proyección (UTM 19S -> WGS84) ---
# EPSG:32719 es UTM Zona 19S (WGS84). EPSG:4326 es el estándar WGS84 Lat/Lon (decimal degrees)
# always_xy=True asegura el orden (Este/Longitud, Norte/Latitud)
transformer = Transformer.from_crs("EPSG:32719", "EPSG:4326", always_xy=True)

def convert_utm_to_wgs84(easting: float, northing: float) -> Tuple[float, float]:
    """ 
    Convierte coordenadas UTM (Chile Central, Zona 19S) a WGS84 Decimal Degrees.
    Retorna: (latitud, longitud)
    """
    # Validación básica para prevenir doble conversión (si ya está en rango decimal)
    if -90 <= northing <= 90 and -180 <= easting <= 180:
        return northing, easting
        
    try:
        # transform(x, y) -> (lon, lat) con always_xy=True
        lon, lat = transformer.transform(easting, northing)
        return lat, lon
    except Exception as e:
        logger.error(f"🚨 Error crítico en conversión de coordenadas UTM ({easting}, {northing}): {str(e)}")
        return 0.0, 0.0

# --- Almacenamiento de Imágenes ---
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_base64_image(base64_string: str, prefix: str) -> Optional[str]:
    """ Decodifica una cadena Base64 y la guarda como archivo .jpg (Legacy) """
    if not base64_string or base64_string.strip() == "":
        return None

    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        import uuid
        filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        img_data = base64.b64decode(base64_string)
        with open(file_path, "wb") as f:
            f.write(img_data)

        logger.info(f"📸 Imagen [ {prefix} ] guardada exitosamente: [ {filename} ]")
        return f"uploads/{filename}"
    except Exception as e:
        logger.exception(f"🚨 Error al decodificar/guardar imagen {prefix}: {str(e)}")
        return None

# --- Fase 120: Advanced Image Organization & Pathing ---

# Mapeo de tipo de foto a nombre de archivo estandarizado
PHOTO_FILENAME_MAP = {
    "general": "general",
    "multiparametro": "multiparametro",
    "turbiedad": "turbiedad",
}

def slugify(text: str) -> str:
    """
    Convierte un nombre de estación en un slug URL-safe.
    Ej: "Estación Río Maipo #1" -> "estacion_rio_maipo_1"
    """
    # 1. Normalizar Unicode (descomponer acentos) y eliminar marcas diacríticas
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # 2. Convertir a minúsculas
    text = text.lower()
    # 3. Reemplazar cualquier carácter no alfanumérico por guión bajo
    text = re.sub(r"[^a-z0-9]+", "_", text)
    # 4. Eliminar guiones bajos al inicio/final y colapsar múltiples
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "sin_nombre"


def save_dynamic_photo(
    b64_string: str,
    fecha: datetime,
    monitoreo_id: int,
    tipo: str,
    station_name: str = "sin_estacion",
) -> Optional[str]:
    """
    Guarda una foto decodificada de Base64 en la estructura profesional:
      static/monitoreos/{year}/{month}/{station_slug}/{monitoring_id}/{tipo}.jpg

    Args:
        b64_string:   Cadena Base64 de la imagen.
        fecha:        Fecha/hora del monitoreo (para year/month).
        monitoreo_id: PK del monitoreo en la BD.
        tipo:         Tipo de foto ('general', 'multiparametro', 'turbiedad').
        station_name: Nombre legible de la estación (se convierte a slug).

    Returns:
        Ruta relativa sin 'static/' para almacenar en la BD,
        o None si hubo error.
    """
    if not b64_string:
        return None

    # 1. Limpiar cabeceras de Base64 si existen
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]

    # 2. Extraer componentes de la fecha
    fecha_ref = fecha if fecha else datetime.now()
    year = fecha_ref.strftime("%Y")
    month = fecha_ref.strftime("%m")
    day = fecha_ref.strftime("%d")

    # 3. Generar slug de la estación
    station_slug = slugify(station_name)

    # 4. Nombre de archivo estandarizado + timestamp para versionado
    base_name = PHOTO_FILENAME_MAP.get(tipo, tipo)
    timestamp = fecha_ref.strftime("%H%M%S")
    file_name = f"{base_name}_{timestamp}.jpg"

    # 5. Construir rutas con pathlib
    #    Ruta relativa (para la BD): monitoreos/2026/04/09/estacion_rio_maipo/35/general_112630.jpg
    relative_folder = Path("monitoreos") / year / month / day / station_slug / str(monitoreo_id)
    relative_path = relative_folder / file_name

    #    Ruta absoluta (en disco): static/monitoreos/2026/04/...
    absolute_folder = Path("static") / relative_folder
    absolute_folder.mkdir(parents=True, exist_ok=True)

    absolute_file_path = absolute_folder / file_name

    # 6. Guardar el archivo físico
    try:
        img_bytes = base64.b64decode(b64_string)
        absolute_file_path.write_bytes(img_bytes)
        # Usar forward-slashes para la ruta guardada en la BD (compatible con URLs)
        db_path = relative_path.as_posix()
        logger.info(f"📸 Foto guardada [{tipo}]: {db_path}")
        return db_path
    except Exception as e:
        logger.exception(f"🚨 Error guardando foto {tipo}: {e}")
        return None
