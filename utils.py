import base64
import os
import re
import unicodedata
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
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
    "caudal": "caudal",
    "nivel_freatico": "nivel_freatico",
    "muestreo": "muestreo",
    "firma": "firma",
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
    data: Union[str, bytes],
    fecha: datetime,
    monitoreo_id: int,
    tipo: str,
    station_name: str = "sin_estacion",
) -> Optional[str]:
    """
    Guarda una foto (en bytes o Base64) en la estructura profesional:
      static/monitoreos/{year}/{month}/{day}/{station_slug}/{monitoring_id}/{tipo}.jpg

    Args:
        data:         Cadena Base64 o bytes de la imagen.
        fecha:        Fecha/hora del monitoreo (para year/month/day).
        monitoreo_id: PK del monitoreo en la BD.
        tipo:         Tipo de foto ('general', 'multiparametro', 'firma', etc).
        station_name: Nombre legible de la estación (se convierte a slug).

    Returns:
        Ruta relativa sin 'static/' para almacenar en la BD,
        o None si hubo error.
    """
    if not data:
        return None

    # 1. Preparar los bytes de la imagen
    img_bytes = None
    try:
        if isinstance(data, bytes):
            img_bytes = data
        else:
            # Es un string Base64, limpiar cabeceras si existen
            if "," in data:
                data = data.split(",")[1]
            img_bytes = base64.b64decode(data)
    except Exception as e:
        logger.error(f"🚨 Error decodificando datos de imagen {tipo}: {e}")
        return None

    if not img_bytes:
        return None

    # 2. Extraer componentes de la fecha
    fecha_ref = fecha if fecha else datetime.now()
    year = fecha_ref.strftime("%Y")
    month = fecha_ref.strftime("%m")
    day = fecha_ref.strftime("%d")

    # 3. Generar slug de la estación
    station_slug = slugify(station_name)

    # 4. Nombre de archivo estandarizado + timestamp para evitar colisiones
    base_name = PHOTO_FILENAME_MAP.get(tipo, tipo)
    timestamp = fecha_ref.strftime("%H%M%S")
    file_name = f"{base_name}_{timestamp}.jpg"

    # 5. Construir rutas con pathlib
    relative_folder = Path("monitoreos") / year / month / day / station_slug / str(monitoreo_id)
    relative_path = relative_folder / file_name

    #    Ruta absoluta (en disco)
    absolute_folder = Path("static") / relative_folder
    absolute_folder.mkdir(parents=True, exist_ok=True)

    absolute_file_path = absolute_folder / file_name

    # 6. Guardar el archivo físico
    try:
        absolute_file_path.write_bytes(img_bytes)
        # Usar forward-slashes para la ruta guardada en la BD
        db_path = relative_path.as_posix()
        logger.info(f"📸 Foto guardada [{tipo}]: {db_path}")
        return db_path
    except Exception as e:
        logger.exception(f"🚨 Error guardando archivo físico {tipo}: {e}")
        return None
