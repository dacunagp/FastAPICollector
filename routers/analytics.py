import math
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
    Fase 97: Obtiene estadísticas para un parámetro dinámico.
    Filtra fallos y detecta outliers usando 5-sigma.
    """
    logger.info(f"📊 Generando analítica para el parámetro: [ {parametro} ]")
    
    # 1. Obtener datos crudos uniendo con Monitoreo para filtrar por fallido
    query = db.query(
        MonitoreoDetalleDB.valor,
        MonitoreoDB.fecha_hora,
        MonitoreoDB.monitoreo_fallido,
        MonitoreoDB.observacion,
        EstacionDB.estacion
    ).join(MonitoreoDB).outerjoin(EstacionDB, MonitoreoDB.estacion_id == EstacionDB.id_estacion).filter(
        MonitoreoDetalleDB.parametro == parametro
    ).all()

    if not query:
        raise HTTPException(status_code=404, detail=f"No hay datos para el parámetro: {parametro}")

    raw_points = []
    clean_values = []

    for row in query:
        val_str, fecha, fallido, obs, est = row
        
        # Intentar convertir valor a float (solo procesamos números para estadística)
        try:
            val_float = float(val_str)
        except (ValueError, TypeError):
            continue

        # Clasificar como "test" si fallido=1 o si la observación contiene palabras clave
        is_test = False
        if fallido == 1:
            is_test = True
        elif obs and any(word in obs.upper() for word in ["TEST", "PRUEBA", "DEMO", "BORRAR"]):
            is_test = True
        
        point = {
            "valor": val_float,
            "fecha": fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else None,
            "estacion": est,
            "is_test": is_test,
            "is_outlier": False
        }
        raw_points.append(point)
        
        # Solo usamos datos limpios (no test) para el baseline estadístico
        if not is_test:
            clean_values.append(val_float)

    # 2. Calcular baseline estadístico (Media y Sigma)
    mean, sigma = calculate_stats(clean_values)
    
    # 3. Identificar outliers (Sanity Check: 5-sigma)
    count_outliers = 0
    for p in raw_points:
        if not p["is_test"] and sigma > 0:
            diff = abs(p["valor"] - mean)
            if diff > (5 * sigma):
                p["is_outlier"] = True
                count_outliers += 1

    logger.info(f"✅ Estadísticas: Clean Mean={mean:.4f}, Clean Sigma={sigma:.4f}. Outliers Detectados: {count_outliers}")

    return {
        "parametro": parametro,
        "media": mean,
        "desviacion_estandar": sigma,
        "puntos": raw_points,
        "count_total": len(raw_points),
        "count_clean": len(clean_values),
        "count_outliers": count_outliers
    }
