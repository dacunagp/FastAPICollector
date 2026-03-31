import base64
import uuid
import os
import logging
from typing import Optional

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
