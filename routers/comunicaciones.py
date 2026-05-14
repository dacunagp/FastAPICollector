import os
import requests
import logging
from fastapi import APIRouter, BackgroundTasks, Request
from schemas import EmailNotificationPayload

router = APIRouter(prefix="/api/comunicaciones", tags=["Comunicaciones"])
logger = logging.getLogger(__name__)

def forward_to_laravel(payload: EmailNotificationPayload):
    """
    Función auxiliar para reenviar la notificación a Laravel en segundo plano.
    """
    # URL de Laravel desde variable de entorno o fallback
    laravel_url = os.getenv("LARAVEL_WEBHOOK_URL", "http://laravel-api.com/api/notificaciones/email")
    
    try:
        logger.info(f"🔄 Reenviando notificación a Laravel (Background): {laravel_url}")
        
        # Usamos timeout para evitar bloqueos prolongados
        response = requests.post(
            laravel_url, 
            json=payload.model_dump(), 
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Notificación reenviada con éxito a Laravel. Status: {response.status_code}")
        else:
            logger.warning(f"⚠️ Laravel respondió con status {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error al reenviar la notificación a Laravel en segundo plano: {str(e)}")

@router.post("/notificar-email")
async def notificar_email(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint que recibe una notificación de email desde la App Flutter
    y la reenvía al backend de Laravel de forma asíncrona.
    """
    body = await request.json()
    logger.info(f"📩 RAW Payload recibido: {body}")
    
    # Validar con el schema manualmente para seguir enviando el payload validado
    payload = EmailNotificationPayload(**body)
    
    # Agregar el reenvío a las tareas en segundo plano
    background_tasks.add_task(forward_to_laravel, payload)
    
    # Retornamos 200 OK inmediatamente
    return {
        "status": "received",
        "message": "Notificación recibida y programada para reenvío"
    }
