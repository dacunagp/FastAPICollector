import logging
import os
from logging.handlers import RotatingFileHandler

# --- Configuración de Logs Narrativos ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "api.log")

# Asegurarse de que el directorio de logs exista
os.makedirs(LOG_DIR, exist_ok=True)

from datetime import datetime

def setup_logging():
    # Agregar una línea de separación física en el archivo de texto para identificar nuevos arranques
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write("\n" + "="*100 + "\n")
            f.write(f"🚀 INICIO DE SESIÓN: {os.path.basename(LOG_FILE)} - {ahora} - PID: {os.getpid()}\n")
            f.write("="*100 + "\n\n")
    except Exception:
        pass

    # Configurar el logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formato narrativo: Fecha - [ NIVEL ] - Mensaje
    formatter = logging.Formatter('%(asctime)s - [ %(levelname)s ] - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Handler para Consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para Archivo (con rotación para no llenar el disco)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info("🚀 Sistema de Logs Narrativos inicializado correctamente.")
