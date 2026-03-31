import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import MonitoreoDB
from schemas import SyncPayload, MuestrasPayload
from auth import verificar_credenciales
from utils import save_base64_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", dependencies=[Depends(verificar_credenciales)])

@router.post("/sync/monitoreos")
def sync_monitoreos(payload: SyncPayload, db: Session = Depends(get_db)):
    """ Recibe array de monitoreos del dispositivo móvil y los guarda con manejo de errores """
    contador_nuevos = 0
    contador_editados = 0
    
    # Log: Inicio de sincronización (Narrativo)
    dispositivo = payload.monitoreos[0].device_id if payload.monitoreos else "DESCONOCIDO"
    logger.info(f"🔄 Iniciando sincronización de registros para el dispositivo: [ {dispositivo} ]")
    
    try:
        for item in payload.monitoreos:
            logger.info(f"📍 Procesando registro móvil [ ID Local: {item.id} ]...")
            
            # 1. Conversión de fechas
            fh = None
            if item.fecha_hora:
                try:
                    fh = datetime.strptime(item.fecha_hora, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Formato de fecha_hora inválido: {item.fecha_hora}")
                
            fh_nivel = None
            if item.fecha_hora_nivel:
                try:
                    fh_nivel = datetime.strptime(item.fecha_hora_nivel, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Formato de fecha_hora_nivel inválido: {item.fecha_hora_nivel}")

            # 1.5 Depuración de fotos recibidas
            print(f"📸 [DEBUG API] ID {item.id} - Principal: {bool(item.foto_path)}, Multi: {bool(item.foto_multiparametro)}, Turb: {bool(item.foto_turbiedad)}")

            # 1.6 Procesar Imágenes (Base64 -> Archivos Físicos)
            # Solo guardamos si el string viene con datos significativos (Base64)
            path_principal = save_base64_image(item.foto_path, "foto") if item.foto_path and len(item.foto_path) > 100 else item.foto_path
            path_multi = save_base64_image(item.foto_multiparametro, "multi") if item.foto_multiparametro and len(item.foto_multiparametro) > 100 else item.foto_multiparametro
            path_turb = save_base64_image(item.foto_turbiedad, "turb") if item.foto_turbiedad and len(item.foto_turbiedad) > 100 else item.foto_turbiedad

            # 2. Verificar si ya existe el registro (Upsert)
            existente = db.query(MonitoreoDB).filter(
                MonitoreoDB.device_id == item.device_id,
                MonitoreoDB.id_local == item.id
            ).first()

            if existente:
                # 3. ACTUALIZAR registro existente (Narrativo)
                logger.info(f"💾 Registro [ ID Local: {item.id} ] - EXISTENTE en la DB. Actualizando datos...")
                existente.programa_id = item.programa_id
                # ... [resto de campos] ...
                existente.estacion_id = item.estacion_id
                existente.fecha_hora = fh
                existente.monitoreo_fallido = item.monitoreo_fallido
                existente.observacion = item.observacion
                existente.matriz_id = item.matriz_id
                existente.equipo_multi_id = item.equipo_multi_id
                existente.turbidimetro_id = item.turbidimetro_id
                existente.metodo_id = item.metodo_id
                existente.hidroquimico = item.hidroquimico
                existente.isotopico = item.isotopico
                existente.cod_laboratorio = item.cod_laboratorio
                existente.usuario_id = item.usuario_id
                existente.is_draft = item.is_draft
                existente.equipo_nivel_id = item.equipo_nivel_id
                existente.tipo_pozo = item.tipo_pozo
                existente.fecha_hora_nivel = fh_nivel
                existente.temperatura = item.temperatura
                existente.ph = item.ph
                existente.conductividad = item.conductividad
                existente.oxigeno = item.oxigeno
                existente.turbiedad = item.turbiedad
                existente.profundidad = item.profundidad
                existente.nivel = item.nivel
                existente.latitud = item.latitud
                existente.longitud = item.longitud
                
                # Mapeo Explicito de Fotos (Usa las rutas de archivos generadas)
                existente.foto_path = path_principal
                existente.foto_multiparametro = path_multi
                existente.foto_turbiedad = path_turb
                contador_editados += 1
            else:
                # 4. CREAR nuevo registro (Narrativo)
                logger.info(f"✨ Registro [ ID Local: {item.id} ] - NUEVO. Insertando en la DB...")
                nuevo_monitoreo = MonitoreoDB(
                    device_id=item.device_id,
                    id_local=item.id, 
                    programa_id=item.programa_id,
                    estacion_id=item.estacion_id,
                    fecha_hora=fh,
                    monitoreo_fallido=item.monitoreo_fallido,
                    observacion=item.observacion,
                    matriz_id=item.matriz_id,
                    equipo_multi_id=item.equipo_multi_id,
                    turbidimetro_id=item.turbidimetro_id,
                    metodo_id=item.metodo_id,
                    hidroquimico=item.hidroquimico,
                    isotopico=item.isotopico,
                    cod_laboratorio=item.cod_laboratorio,
                    usuario_id=item.usuario_id,
                    is_draft=item.is_draft,
                    equipo_nivel_id=item.equipo_nivel_id,
                    tipo_pozo=item.tipo_pozo,
                    fecha_hora_nivel=fh_nivel,
                    temperatura=item.temperatura,
                    ph=item.ph,
                    conductividad=item.conductividad,
                    oxigeno=item.oxigeno,
                    turbiedad=item.turbiedad,
                    profundidad=item.profundidad,
                    nivel=item.nivel,
                    latitud=item.latitud,
                    longitud=item.longitud,
                    foto_path=path_principal,
                    foto_multiparametro=path_multi,
                    foto_turbiedad=path_turb
                )
                db.add(nuevo_monitoreo)
                contador_nuevos += 1
            
        # 3. Intento de persistencia en MySQL
        db.commit() 
        logger.info(f"🚀 Sincronización Finalizada de forma exitosa. Se detectaron {contador_nuevos} nuevos y {contador_editados} editados.")
        
        return {
            "status": "success",
            "mensaje": f"Se sincronizaron con éxito {contador_nuevos} nuevos y {contador_editados} ya existentes."
        }

    except Exception as e:
        db.rollback() 
        logger.exception(f"🚨 ERROR CRÍTICO EN SYNC: {str(e)}") 
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno en el servidor/DB (Consulta el log de la API)"
        )

@router.post("/muestras")
def exponer_muestras(payload: MuestrasPayload, db: Session = Depends(get_db)):
    """ Recibe un programa y un array de estaciones """
    return {
        "status": "success",
        "mensaje": "Búsqueda procesada",
        "programa_solicitado": payload.programa,
        "estaciones_solicitadas": payload.estaciones
    }
