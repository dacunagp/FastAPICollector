import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

security = HTTPBasic()

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    usuario_correcto = secrets.compare_digest(credentials.username, "collector")
    password_correcto = secrets.compare_digest(credentials.password, "gp2026")
    if not (usuario_correcto and password_correcto):
        logger.warning(f"❌ Intento de acceso fallido para el usuario: [{credentials.username}]")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Log de acceso exitoso (Narrativo)
    logger.info(f"🔑 Acceso concedido al usuario: [{credentials.username}]")
    return credentials.username
