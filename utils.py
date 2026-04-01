import base64
import uuid
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Almacenamiento de Imágenes ---
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_base64_image(base64_string: str, prefix: str) -> Optional[str]:
    """ Decodifica una cadena Base64 y la guarda como archivo .jpg """
    if not base64_string or base64_string.strip() == "":
        return None

    try:
        # 1. Limpiar cabeceras si existen (ej: data:image/jpeg;base64,)
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        # 2. Generar nombre único
        filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 3. Decodificar y Guardar
        img_data = base64.b64decode(base64_string)
        with open(file_path, "wb") as f:
            f.write(img_data)

        # 4. Retornar ruta relativa para la base de datos
        logger.info(f"📸 Imagen [ {prefix} ] guardada exitosamente: [ {filename} ]")
        return f"uploads/{filename}"
    except Exception as e:
        logger.exception(f"🚨 Error al decodificar/guardar imagen {prefix}: {str(e)}")
        return None

# Directorio base del servidor (donde se guardan los archivos físicamente)
BASE_UPLOAD_DIR = "static" 

def save_dynamic_photo(b64_string: str, device_id: str, fecha: datetime, monitoreo_id: int, tipo: str) -> Optional[str]:
    if not b64_string:
        return None
        
    # Limpiar cabeceras de Base64 si existen
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]

    # Extraer Año y Mes
    year = fecha.strftime("%Y") if fecha else datetime.now().strftime("%Y")
    month = fecha.strftime("%m") if fecha else datetime.now().strftime("%m")
    
    # Construir la ruta relativa exacta (la que se guarda en la BD)
    # Ej: monitoreos/MOBILE-DATA/2026/03/monitoreo_35/general_a1b2.jpg
    relative_folder = f"monitoreos/{device_id}/{year}/{month}/monitoreo_{monitoreo_id}"
    file_name = f"{tipo}_{uuid.uuid4().hex[:8]}.jpg"
    relative_path = f"{relative_folder}/{file_name}"
    
    # Construir la ruta absoluta (para el sistema operativo)
    absolute_folder = os.path.join(BASE_UPLOAD_DIR, relative_folder)
    os.makedirs(absolute_folder, exist_ok=True) # Crea todas las carpetas si no existen
    
    absolute_file_path = os.path.join(absolute_folder, file_name)
    
    # Guardar el archivo físico
    try:
        with open(absolute_file_path, "wb") as f:
            f.write(base64.b64decode(b64_string))
        logger.info(f"📸 Foto dinámica guardada: {relative_path}")
        return relative_path
    except Exception as e:
        logger.exception(f"🚨 Error guardando foto {tipo}: {e}")
        return None
