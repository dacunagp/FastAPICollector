import os
import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

security = HTTPBasic()

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    # Obtener credenciales desde el entorno
    api_usernames = os.getenv("API_USERNAMES", "gpconsul,collector").split(",")
    api_password = os.getenv("API_PASSWORD", "gp2026")

    usuario_valido = credentials.username in api_usernames
    password_correcto = secrets.compare_digest(credentials.password, api_password)
    
    if not (usuario_valido and password_correcto):
        logger.warning(f"❌ Intento de acceso fallido para el usuario: [{credentials.username}]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Log de acceso exitoso (Narrativo)
    logger.info(f"🔑 Acceso concedido al usuario: [{credentials.username}]")
    return credentials.username
