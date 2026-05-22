import logging
import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import AuditLogDB, UsuarioDB, EstacionDB, EquipoDB
from schemas import AuditLog
from auth import verificar_credenciales
from utils import get_chile_time
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Audit"], dependencies=[Depends(verificar_credenciales)])


# --- Schema para recibir logs desde la app móvil ---
class AuditLogAppItem(BaseModel):
    local_id: Optional[str] = None       # ID que asigna la app (para rastreo)
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    accion: Optional[str] = "update"
    modulo: Optional[str] = "app_collector"
    registro_id: Optional[int] = None
    registro_ref: Optional[str] = None
    cambios: Optional[str] = None
    created_at: Optional[str] = None

class AuditSyncPayload(BaseModel):
    logs: List[AuditLogAppItem]


@router.get("/logs", response_model=List[AuditLog])
def get_audit_logs(db: Session = Depends(get_db)):
    """
    Retorna el historial de auditoría.
    """
    logger.info("📊 Consulta de logs de auditoría solicitada.")
    return db.query(AuditLogDB).order_by(AuditLogDB.created_at.desc()).limit(100).all()

@router.get("/summary")
def get_audit_summary(db: Session = Depends(get_db)):
    """
    Retorna un resumen formateado de los logs para el dashboard.
    Incluye traducción de IDs a etiquetas legibles.
    """
    logs = db.query(AuditLogDB).order_by(AuditLogDB.created_at.desc()).limit(50).all()
    summary = []
    
    for log in logs:
        detalle_obj = {}
        try:
            detalle_obj = json.loads(log.cambios) if log.cambios else {}
        except:
            detalle_obj = {"raw": log.cambios}

        # Intentar humanizar el log
        usuario = log.usuario.nombre if log.usuario else "Sistema"
        
        # Traducir IDs si existen en detalles
        estacion_label = "N/A"
        if "estacion_id" in detalle_obj:
            est = db.query(EstacionDB).filter(EstacionDB.id_estacion == detalle_obj["estacion_id"]).first()
            estacion_label = est.estacion if est else f"ID {detalle_obj['estacion_id']}"
        
        equipo_label = "N/A"
        if "equipo_id" in detalle_obj:
            eq = db.query(EquipoDB).filter(EquipoDB.id_equipo == detalle_obj["equipo_id"]).first()
            equipo_label = eq.codigo_equipo if eq else f"ID {detalle_obj['equipo_id']}"

        msg = f"Acción: {log.accion} | Módulo: {log.modulo or 'N/A'}"
        
        summary.append({
            "id": log.id,
            "fecha": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
            "usuario": log.usuario_nombre or usuario,
            "accion": log.accion,
            "modulo": log.modulo,
            "estacion": estacion_label,
            "equipo": equipo_label,
            "detalles": detalle_obj,
            "human_msg": msg
        })
        
    return summary


@router.post("/sync")
def sync_audit_from_app(payload: AuditSyncPayload, request: Request, db: Session = Depends(get_db)):
    """
    Recibe logs de trazabilidad desde la app móvil (GPCollector) y los inserta en audit_logs.
    Endpoint: POST /api/audit/sync
    """
    if not payload.logs:
        return {"status": "error", "message": "No se recibieron logs.", "saved": []}

    ahora = get_chile_time()
    insertados = 0
    saved = []  # Mapeo local_id → id_unica para cada log guardado

    for item in payload.logs:
        try:
            created = ahora
            if item.created_at:
                try:
                    created = datetime.fromisoformat(item.created_at)
                except Exception:
                    created = ahora

            nuevo_log = AuditLogDB(
                usuario_id=item.usuario_id,
                usuario_nombre=item.usuario_nombre or "App GPCollector",
                accion=item.accion or "update",
                modulo=item.modulo or "app_collector",
                registro_id=item.registro_id,
                registro_ref=item.registro_ref,
                cambios=item.cambios,
                ip_address=request.client.host if request.client else None,
                created_at=created,
            )
            db.add(nuevo_log)
            db.flush()  # Obtener el id generado por la BD antes del commit

            saved.append({
                "local_id": item.local_id,       # ID enviado por la app
                "id_unica": nuevo_log.id          # ID asignado por el servidor
            })
            insertados += 1
        except Exception as e:
            logger.error(f"⚠️ Error insertando log de app: {str(e)}")

    db.commit()
    logger.info(f"✅ [AUDIT SYNC] {insertados} logs recibidos desde la app GPCollector.")
    return {
        "status": "ok",
        "insertados": insertados,
        "saved": saved  # ✅ Mapeo de IDs locales vs IDs del servidor
    }
