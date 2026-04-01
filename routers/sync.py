import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import MonitoreoDB, MonitoreoFotoDB
from schemas import SyncPayload, MuestrasPayload
from auth import verificar_credenciales
from utils import save_base64_image, save_dynamic_photo

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

            # 2. Verificar si ya existe el registro (Upsert Robust)
            # Buscamos por la llave compuesta (id_local + device_id)
            existente = db.query(MonitoreoDB).filter(
                MonitoreoDB.id_local == item.id,
                MonitoreoDB.device_id == item.device_id
            ).first()

            nuevo_monitoreo = None

            if existente:
                # 3. ACTUALIZAR registro existente (Narrativo)
                logger.info(f"💾 Registro [ ID Local: {item.id} ] - EXISTENTE. Actualizando todos los campos...")
                existente.programa_id = item.programa_id
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
                    longitud=item.longitud
                )
                db.add(nuevo_monitoreo)
                contador_nuevos += 1
            
            # --- NUEVA LÓGICA DE FOTOS (Fase 39) ---
            db.flush() # Obtenemos el ID real generado en la tabla principal
            db_monitoreo_id = existente.id if existente else nuevo_monitoreo.id
            
            # Fecha base para las carpetas
            fecha_base = fh if fh else datetime.now()

            # Diccionario para mapear los campos del JSON a los "tipos" de la BD
            fotos_a_procesar = {
                'general': item.foto_path,
                'multiparametro': item.foto_multiparametro,
                'turbiedad': item.foto_turbiedad
            }

            for tipo, b64_data in fotos_a_procesar.items():
                if b64_data and len(b64_data) > 100: # Solo si hay datos significativos
                    # Verificar si ya existe en la BD
                    foto_existente = db.query(MonitoreoFotoDB).filter(
                        MonitoreoFotoDB.monitoreo_id == db_monitoreo_id,
                        MonitoreoFotoDB.tipo == tipo
                    ).first()

                    # Guardar el archivo en el disco y obtener la ruta formateada
                    ruta_guardada = save_dynamic_photo(b64_data, item.device_id, fecha_base, db_monitoreo_id, tipo)

                    if ruta_guardada:
                        if foto_existente:
                            foto_existente.ruta = ruta_guardada
                        else:
                            nueva_foto = MonitoreoFotoDB(
                                monitoreo_id=db_monitoreo_id,
                                tipo=tipo,
                                ruta=ruta_guardada
                            )
                            db.add(nueva_foto)
            
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
