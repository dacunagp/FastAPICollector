import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, Depends, HTTPException, status
from auth import verificar_credenciales
from schemas import EmailRequest
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

router = APIRouter(prefix="/api", tags=["Email"])

logger = logging.getLogger(__name__)

@router.post("/enviar-correo")
def enviar_correo(
    request: EmailRequest,
    username: str = Depends(verificar_credenciales)
):
    # 1. Log de recepción
    logger.info(f"📩 Recibida solicitud de correo para: [{request.destinatario}]")
    
    # 2. Log de detalles (Asunto y longitud del cuerpo)
    logger.info(f"📋 Asunto: {request.asunto} | Longitud del cuerpo: {len(request.cuerpo)} caracteres")

    # Configuración desde variables de entorno
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not all([smtp_server, smtp_user, smtp_password]):
        error_msg = "Configuración SMTP incompleta en el servidor"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

    try:
        # Preparar el mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = request.destinatario
        msg['Subject'] = request.asunto
        msg.attach(MIMEText(request.cuerpo, 'plain'))

        # Proceso SMTP con logs detallados
        logger.info(f"🔄 Conectando al servidor SMTP: {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Asegurar conexión cifrada
        
        logger.info(f"🔑 Autenticando como: {smtp_user}...")
        server.login(smtp_user, smtp_password)
        
        logger.info(f"📧 Enviando correo a: {request.destinatario}...")
        server.send_message(msg)
        
        server.quit()
        
        logger.info(f"✅ Correo enviado con éxito a {request.destinatario}")
        return {
            "status": "success",
            "message": f"Correo enviado correctamente a {request.destinatario}"
        }

    except Exception as e:
        # 3. Log de error con Traceback completo
        full_error = traceback.format_exc()
        logger.error(f"❌ Error al enviar correo:\n{full_error}")
        
        # El servidor responde con el detalle del error para la App móvil
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": full_error if os.getenv("DEBUG") == "True" else "Consulte los logs del servidor"
            }
        )
