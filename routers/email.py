import os
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from fastapi import APIRouter, Depends, HTTPException, status
from auth import verificar_credenciales
from schemas import EmailRequest
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from database import get_db
from sqlalchemy.orm import Session
from utils import log_audit

router = APIRouter(prefix="/api", tags=["Email"])

logger = logging.getLogger(__name__)

@router.post("/enviar-correo")
def enviar_correo(
    request: EmailRequest,
    db: Session = Depends(get_db),
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
        # Preparar el mensaje principal como 'related' para soportar imágenes incrustadas
        msg = MIMEMultipart('related')
        msg['From'] = smtp_from
        msg['To'] = request.destinatario
        
        asunto_con_prefijo = f"Notificación: {request.asunto}"
        msg['Subject'] = asunto_con_prefijo

        # Crear alternativa para texto plano y HTML
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # 1. Versión en texto plano (fallback)
        text_plain = f"{asunto_con_prefijo}\n\nDetalles técnicos:\n\n{request.cuerpo}"
        msg_alternative.attach(MIMEText(text_plain, 'plain'))

        # 2. Versión en HTML
        # Convertir los saltos de línea a <br> para el HTML
        cuerpo_html = request.cuerpo.replace('\n', '<br>')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    color: #333333;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                }}
                .email-container {{
                    max-width: 650px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-top: 5px solid #0EA5E9; /* Azul de GP */
                    padding: 30px;
                }}
                .title {{
                    color: #2563EB;
                    font-size: 20px;
                    font-weight: 600;
                    margin: 0;
                }}
                .subtitle {{
                    font-size: 11px;
                    color: #888888;
                    text-transform: uppercase;
                    margin-top: 5px;
                }}
                .body-content {{
                    font-size: 14px;
                    line-height: 1.6;
                    color: #444444;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #f0f0f0;
                    font-size: 13px;
                    color: #666666;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; margin-bottom: 25px;">
                    <tr>
                        <td width="70%" valign="top">
                            <h2 class="title">{request.asunto}</h2>
                            <div class="subtitle">SISTEMA GP COLLECTOR</div>
                        </td>
                        <td width="30%" align="right" valign="top">
                            <!-- Logo incrustado vía CID -->
                            <img src="cid:logo_gp" alt="GP Consultores" style="max-width: 140px; height: auto;">
                        </td>
                    </tr>
                </table>
                
                <div class="body-content">
                    <p style="margin-top: 0; margin-bottom: 10px; color: #555555;"><strong>Detalles técnicos:</strong></p>
                    {cuerpo_html}
                </div>
                
                <div class="footer">
                    <p>Saludos cordiales,<br>
                    <strong>GP Collector</strong><br>
                    GP Consultores - Recursos Hídricos & Medio Ambiente</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg_alternative.attach(MIMEText(html_content, 'html'))

        # 3. Adjuntar la imagen del logo (CID)
        logo_path = "static/gp_icon_email.png"
        try:
            with open(logo_path, "rb") as f:
                img_data = f.read()
            logo_img = MIMEImage(img_data)
            logo_img.add_header('Content-ID', '<logo_gp>')
            logo_img.add_header('Content-Disposition', 'inline', filename='gp_icon_email.png')
            msg.attach(logo_img)
        except FileNotFoundError:
            logger.warning(f"⚠️ Logo no encontrado en {logo_path}. El correo se enviará sin imagen incrustada.")

        # Proceso SMTP con logs detallados
        logger.info(f"🔄 Conectando al servidor SMTP: {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Asegurar conexión cifrada
        
        logger.info(f"🔑 Autenticando como: {smtp_user}...")
        server.login(smtp_user, smtp_password)
        server.send_message(msg) # Faltaba esta línea para enviar el mensaje real
        server.quit()
        
        logger.info(f"✅ Correo enviado con éxito a {request.destinatario}")
        
        # Auditoría
        try:
            from models import UsuarioDB
            usuario = db.query(UsuarioDB).filter(UsuarioDB.nombre == username).first()
            user_id = usuario.id_usuario if usuario else None
            
            log_audit(
                db=db,
                usuario_id=user_id,
                accion="EMAIL_SENT",
                tabla="correos",
                detalles={
                    "destinatario": request.destinatario,
                    "asunto": request.asunto
                }
            )
            db.commit()
        except Exception as audit_err:
            logger.error(f"⚠️ No se pudo registrar auditoría de correo: {audit_err}")

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