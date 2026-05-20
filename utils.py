import base64
import os
import re
import unicodedata
import logging
import boto3
import io
import json
from pathlib import Path
from typing import Optional, Tuple, Union
from datetime import datetime
from zoneinfo import ZoneInfo
from pyproj import Transformer
from sqlalchemy.orm import Session

def get_chile_time():
    """Retorna la hora actual en Chile (America/Santiago) para almacenamiento en DB."""
    return datetime.now(ZoneInfo("America/Santiago")).replace(tzinfo=None)

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

# --- Configuración AWS S3 ---
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_BUCKET = os.getenv("AWS_BUCKET")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

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
    id_equipo: str = "0",
    id_punto: str = "0",
    content_type: str = "image/jpeg"
) -> Optional[str]:
    """
    Sube una foto (en bytes o Base64) a Amazon S3 en la estructura profesional:
      monitoreos/{year}/{month}/{day}/{id_equipo}/{id_punto}/{filename}

    Returns:
        URL pública de S3 para almacenar en la BD, o None si hubo error.
    """
    if not data:
        return None

    # 1. Preparar los bytes de la imagen
    img_bytes = None
    try:
        if isinstance(data, bytes):
            img_bytes = data
        else:
            if "," in data:
                data = data.split(",")[1]
            img_bytes = base64.b64decode(data)
    except Exception as e:
        logger.error(f"🚨 Error decodificando datos de imagen {tipo}: {e}")
        return None

    if not img_bytes:
        return None

    # 2. Extraer componentes de la fecha
    fecha_ref = fecha if fecha else get_chile_time()
    year = fecha_ref.strftime("%Y")
    month = fecha_ref.strftime("%m")
    day = fecha_ref.strftime("%d")

    # 3. Nombre de archivo estandarizado + timestamp para evitar colisiones
    base_name = PHOTO_FILENAME_MAP.get(tipo, tipo)
    timestamp = fecha_ref.strftime("%H%M%S")
    file_name = f"{base_name}_{timestamp}.jpg"

    # 4. Construir S3 Key: monitoreos/YYYY/MM/DD/[id_equipo]/[id_punto]/[filename]
    s3_key = f"monitoreos/{year}/{month}/{day}/{id_equipo}/{id_punto}/{file_name}"

    # 5. Subir a S3 usando upload_fileobj para streaming
    try:
        file_obj = io.BytesIO(img_bytes)
        s3_client.upload_fileobj(
            file_obj,
            AWS_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        
        # 6. Construir URL pública
        public_url = f"https://{AWS_BUCKET}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"🚀 Foto subida a S3 [{tipo}]: {public_url}")
        return public_url

    except Exception as e:
        logger.exception(f"🚨 Error subiendo archivo a S3 {tipo}: {e}")
        return None

def log_audit(db: Session, usuario_id: Optional[int], accion: str, tabla: str, registro_id: Optional[int] = None, detalles: Optional[Union[dict, str]] = None, usuario_nombre: Optional[str] = None):
    """
    Registra una acción en la tabla de auditoría para trazabilidad.
    """
    from models import AuditLogDB
    try:
        if isinstance(detalles, dict):
            detalles = json.dumps(detalles, ensure_ascii=False)
        
        nuevo_log = AuditLogDB(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion=accion,
            modulo='web_admin',      # Los logs internos del servidor son del módulo web
            registro_id=registro_id,
            cambios=detalles         # Ahora mapea correctamente al campo 'cambios'
        )
        db.add(nuevo_log)
        # Se asume que el commit lo hará la función llamadora
    except Exception as e:
        logger.error(f"⚠️ Error al crear log de auditoría: {str(e)}")
