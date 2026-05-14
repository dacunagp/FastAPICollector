import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AuditLogDB, UsuarioDB, EstacionDB, EquipoDB
from schemas import AuditLog
from auth import verificar_credenciales

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Audit"], dependencies=[Depends(verificar_credenciales)])

@router.get("/logs", response_model=List[AuditLog])
def get_audit_logs(db: Session = Depends(get_db)):
    """
    Retorna el historial de auditoría.
    """
    logger.info("📊 Consulta de logs de auditoría solicitada.")
    return db.query(AuditLogDB).order_by(AuditLogDB.fecha_hora.desc()).limit(100).all()

@router.get("/summary")
def get_audit_summary(db: Session = Depends(get_db)):
    """
    Retorna un resumen formateado de los logs para el dashboard.
    Incluye traducción de IDs a etiquetas legibles.
    """
    logs = db.query(AuditLogDB).order_by(AuditLogDB.fecha_hora.desc()).limit(50).all()
    summary = []
    
    for log in logs:
        detalle_obj = {}
        try:
            import json
            detalle_obj = json.loads(log.detalles) if log.detalles else {}
        except:
            detalle_obj = {"raw": log.detalles}

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

        msg = f"Acción: {log.accion} en tabla {log.tabla}"
        if log.accion == "BULK_SYNC":
            msg = f"Sincronización masiva: {detalle_obj.get('nuevos', 0)} nuevos, {detalle_obj.get('editados', 0)} editados."
        
        summary.append({
            "id": log.id,
            "fecha": log.fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": usuario,
            "accion": log.accion,
            "tabla": log.tabla,
            "estacion": estacion_label,
            "equipo": equipo_label,
            "detalles": detalle_obj,
            "human_msg": msg
        })
        
    return summary
