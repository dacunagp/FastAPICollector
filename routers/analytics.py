import math
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MonitoreoDB, MonitoreoDetalleDB, EstacionDB
from schemas import AnalyticsResponse, AnalyticsPoint
from auth import verificar_credenciales

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", dependencies=[Depends(verificar_credenciales)])

def calculate_stats(values):
    """ Calcula media y desviación estándar poblacional """
    if not values:
        return 0.0, 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)
    return mean, std_dev

@router.get("/{parametro}", response_model=AnalyticsResponse)
def get_analytics(parametro: str, db: Session = Depends(get_db)):
    """ 
    Fase 125: Obtiene estadísticas para un parámetro dinámico.
    Soporta tanto la tabla legacy (MonitoreoDetalleDB) como los nuevos documentos JSON.
    Filtra fallos y detecta outliers usando 5-sigma.
    """
    logger.info(f"📊 Generando analítica para el parámetro: [ {parametro} ]")
    
    raw_points = []
    clean_values = []
    detected_unit = None

    # 1. Obtener datos de la tabla legacy (MonitoreoDetalleDB)
    legacy_rows = db.query(
        MonitoreoDetalleDB.valor,
        MonitoreoDB.fecha_hora,
        MonitoreoDB.monitoreo_fallido,
        MonitoreoDB.observacion,
        EstacionDB.estacion,
        MonitoreoDB.fecha_hora_muestreo
    ).join(MonitoreoDB).outerjoin(EstacionDB, MonitoreoDB.estacion_id == EstacionDB.id_estacion).filter(
        MonitoreoDetalleDB.parametro == parametro
    ).all()

    for row in legacy_rows:
        val_str, fecha, fallido, obs, est = row
        try:
            val_float = float(val_str)
            raw_points.append({
                "valor": val_float,
                "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else None,
                "estacion": est,
                "is_test": bool(fallido == 1 or (obs and any(word in obs.upper() for word in ["TEST", "PRUEBA", "DEMO", "BORRAR"]))),
                "is_outlier": False,
                "fecha_hora_muestreo": row.fecha_hora_muestreo.strftime("%Y-%m-%d %H:%M:%S") if row.fecha_hora_muestreo else None
            })
        except: continue

    # 2. Obtener datos de los nuevos campos JSON (detalles_json y multiparametros_json)
    json_rows = db.query(
        MonitoreoDB.detalles_json,
        MonitoreoDB.multiparametros_json,
        MonitoreoDB.fecha_hora,
        MonitoreoDB.monitoreo_fallido,
        MonitoreoDB.observacion,
        EstacionDB.estacion,
        MonitoreoDB.fecha_hora_muestreo
    ).outerjoin(EstacionDB, MonitoreoDB.estacion_id == EstacionDB.id_estacion).filter(
        (MonitoreoDB.detalles_json.isnot(None)) | (MonitoreoDB.multiparametros_json.isnot(None))
    ).all()

    for row in json_rows:
        detalles_raw, multi_raw, fecha, fallido, obs, est = row
        
        # Combinar ambos arrays JSON para buscar el parámetro
        items = []
        try:
            if detalles_raw: items.extend(json.loads(detalles_raw))
            if multi_raw: items.extend(json.loads(multi_raw))
        except: continue

        for item in items:
            if isinstance(item, dict) and item.get("parametro") == parametro:
                try:
                    val_float = float(item.get("valor"))
                    raw_points.append({
                        "valor": val_float,
                        "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else None,
                        "estacion": est,
                        "is_test": bool(fallido == 1 or (obs and any(word in obs.upper() for word in ["TEST", "PRUEBA", "DEMO", "BORRAR"]))),
                        "is_outlier": False,
                        "fecha_hora_muestreo": row.fecha_hora_muestreo.strftime("%Y-%m-%d %H:%M:%S") if row.fecha_hora_muestreo else None
                    })
                    if item.get("unidad"):
                        detected_unit = item.get("unidad")
                except: continue

    if not raw_points:
        raise HTTPException(status_code=404, detail=f"No hay datos para el parámetro: {parametro}")

    # 3. Calcular baseline estadístico (Media y Sigma) usando solo puntos que no son test
    clean_values = [p["valor"] for p in raw_points if not p["is_test"]]
    mean, sigma = calculate_stats(clean_values)
    
    # 4. Identificar outliers (Sanity Check: 5-sigma)
    count_outliers = 0
    for p in raw_points:
        if not p["is_test"] and sigma > 0:
            diff = abs(p["valor"] - mean)
            if diff > (5 * sigma):
                p["is_outlier"] = True
                count_outliers += 1

    logger.info(f"✅ Analítica completada. Puntos: {len(raw_points)}, Media: {mean:.2f}, Unidad: {detected_unit}")

    return {
        "parametro": parametro,
        "unidad": detected_unit,
        "media": mean,
        "desviacion_estandar": sigma,
        "puntos": raw_points,
        "count_total": len(raw_points),
        "count_clean": len(clean_values),
        "count_outliers": count_outliers
    }
