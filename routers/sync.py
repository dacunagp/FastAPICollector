import logging
import json
import requests as req
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import MonitoreoDB, MonitoreoFotoDB, EstacionDB, MonitoreoDetalleDB
from schemas import SyncPayload, MuestrasPayload
from auth import verificar_credenciales
from utils import save_dynamic_photo, convert_utm_to_wgs84

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
    logger.debug(f"📦 Payload completo recibido: {payload.model_dump_json()}")
    
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
                    
            fh_caudal = None
            if item.fecha_hora_caudal:
                try:
                    fh_caudal = datetime.strptime(item.fecha_hora_caudal, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Formato de fecha_hora_caudal inválido: {item.fecha_hora_caudal}")

            # 1.5 Depuración de fotos recibidas
            print(f"📸 [DEBUG API] ID {item.id} - Principal: {bool(item.foto_path)}, Multi: {bool(item.foto_multiparametro)}, Turb: {bool(item.foto_turbiedad)}, Cau: {bool(item.foto_caudal)}, Nivel: {bool(item.foto_nivel_freatico)}, Muestreo: {bool(item.foto_muestreo)}")

            # --- Log de la información a registrar (sin fotos en base64) ---
            item_dict = item.model_dump()
            claves_a_limpiar = [
                "foto_path", "foto_multiparametro", "foto_turbiedad", 
                "foto_caudal", "foto_nivel_freatico", "foto_muestreo"
            ]
            for clave in claves_a_limpiar:
                if item_dict.get(clave):
                    item_dict[clave] = "[FOTO_BASE64_OMITIDA]"
                    
            logger.info(f"📥 Información a procesar para la Base de Datos [ID Local: {item.id}]:\n{json.dumps(item_dict, indent=2, ensure_ascii=False)}")

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
                existente.equipo_caudal = item.equipo_caudal
                existente.nivel_caudal = item.nivel_caudal
                existente.fecha_hora_caudal = fh_caudal
                existente.turbiedad = item.turbiedad
                existente.profundidad = item.profundidad
                existente.nivel = item.nivel
                existente.latitud = item.latitud
                existente.longitud = item.longitud
                
                # Fase 108: Pivot a JSON Document
                if item.detalles_json is not None:
                    existente.detalles_json = json.dumps(item.detalles_json) if not isinstance(item.detalles_json, str) else item.detalles_json
                
                # Fase 113: Backend Support for Dual JSON Architecture
                existente.multiparametros_json = json.dumps(item.multiparametros_json) if isinstance(item.multiparametros_json, (list, dict)) else item.multiparametros_json
                
                logger.debug(f"📝 [UPDATE] ID {item.id} - detalles_json: {existente.detalles_json[:100]}... | multiparametros_json: {existente.multiparametros_json[:100]}...")
                
                # --- Fase 115: Asignar fotos (Base64 original) procedentes del payload ---
                existente.foto_path = item.foto_path
                existente.foto_multiparametro = item.foto_multiparametro
                existente.foto_turbiedad = item.foto_turbiedad
                existente.foto_caudal = item.foto_caudal
                existente.foto_nivel_freatico = item.foto_nivel_freatico
                existente.foto_muestreo = item.foto_muestreo
                
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
                    equipo_caudal=item.equipo_caudal,
                    nivel_caudal=item.nivel_caudal,
                    fecha_hora_caudal=fh_caudal,
                    turbiedad=item.turbiedad,
                    profundidad=item.profundidad,
                    nivel=item.nivel,
                    latitud=item.latitud,
                    longitud=item.longitud,
                    # Fase 108: Pivot a JSON Document
                    detalles_json=json.dumps(item.detalles_json) if not isinstance(item.detalles_json, str) else item.detalles_json,
                    # Fase 113: Backend Support for Dual JSON Architecture
                    multiparametros_json=json.dumps(item.multiparametros_json) if isinstance(item.multiparametros_json, (list, dict)) else item.multiparametros_json,
                    # --- Fase 115: Asignar fotos (Base64 original) procedentes del payload ---
                    foto_path=item.foto_path,
                    foto_multiparametro=item.foto_multiparametro,
                    foto_turbiedad=item.foto_turbiedad,
                    foto_caudal=item.foto_caudal,
                    foto_nivel_freatico=item.foto_nivel_freatico,
                    foto_muestreo=item.foto_muestreo
                )
                db.add(nuevo_monitoreo)
                logger.debug(f"📝 [INSERT] ID {item.id} - detalles_json: {nuevo_monitoreo.detalles_json[:100]}... | multiparametros_json: {nuevo_monitoreo.multiparametros_json[:100]}...")
                contador_nuevos += 1
            
            # --- FASE 120: Advanced Image Organization & Pathing ---
            db.flush() # Obtenemos el ID real generado en la tabla principal
            db_monitoreo_id = existente.id if existente else nuevo_monitoreo.id
            
            # Fecha base para las carpetas
            fecha_base = fh if fh else datetime.now()

            # Obtener nombre de la estación para el slug de la carpeta
            station_name = "sin_estacion"
            if item.estacion_id:
                estacion_obj = db.query(EstacionDB).filter(EstacionDB.id_estacion == item.estacion_id).first()
                if estacion_obj and estacion_obj.estacion:
                    station_name = estacion_obj.estacion

            # Diccionario para mapear los campos del JSON a los "tipos" de la BD
            fotos_a_procesar = {
                'general': item.foto_path,
                'multiparametro': item.foto_multiparametro,
                'turbiedad': item.foto_turbiedad,
                'caudal': item.foto_caudal,
                'nivel_freatico': item.foto_nivel_freatico,
                'muestreo': item.foto_muestreo
            }

            for tipo, b64_data in fotos_a_procesar.items():
                if b64_data and len(b64_data) > 100: # Solo si hay datos significativos
                    # Verificar si ya existe en la BD
                    foto_existente = db.query(MonitoreoFotoDB).filter(
                        MonitoreoFotoDB.monitoreo_id == db_monitoreo_id,
                        MonitoreoFotoDB.tipo == tipo
                    ).first()

                    # Guardar el archivo en el disco con estructura profesional
                    ruta_guardada = save_dynamic_photo(b64_data, fecha_base, db_monitoreo_id, tipo, station_name)

                    if ruta_guardada:
                        # 1. Guardar en la tabla de fotos (Legacy support)
                        if foto_existente:
                            foto_existente.ruta = ruta_guardada
                        else:
                            nueva_foto = MonitoreoFotoDB(
                                monitoreo_id=db_monitoreo_id,
                                tipo=tipo,
                                ruta=ruta_guardada
                            )
                            db.add(nueva_foto)
                        
                        # 2. Sincronizar en el registro principal (Fase 86)
                        monitoreo_obj = existente if existente else nuevo_monitoreo
                        if tipo == 'general': monitoreo_obj.foto_path = ruta_guardada
                        elif tipo == 'multiparametro': monitoreo_obj.foto_multiparametro = ruta_guardada
                        elif tipo == 'turbiedad': monitoreo_obj.foto_turbiedad = ruta_guardada
                        elif tipo == 'caudal': monitoreo_obj.foto_caudal = ruta_guardada
                        elif tipo == 'nivel_freatico': monitoreo_obj.foto_nivel_freatico = ruta_guardada
                        elif tipo == 'muestreo': monitoreo_obj.foto_muestreo = ruta_guardada
            
            # --- NUEVA LÓGICA DE DETALLES/PARÁMETROS EXTRA (Fase 86) ---
            if item.detalles:
                logger.info(f"💾 Guardando {len(item.detalles)} parámetros extra (detalles) para el monitoreo...")
                # Si es un edit, limpiamos los detalles previos (Full Sync)
                if existente:
                    db.query(MonitoreoDetalleDB).filter(MonitoreoDetalleDB.monitoreo_id == db_monitoreo_id).delete()
                
                for det in item.detalles:
                    db_detalle = MonitoreoDetalleDB(
                        monitoreo_id=db_monitoreo_id,
                        parametro=det.parametro,
                        valor=det.valor,           # Fase 88: ahora es String
                        tipo_dato=det.tipo_dato     # Fase 88: "number", "text", "boolean"
                    )
                    db.add(db_detalle)
            
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
def exponer_muestras(payload: MuestrasPayload, request: Request):
    """ Proxy hacia la API externa: reenvía la consulta de historial de muestras con autenticación """
    URL_EXTERNA = "http://apicollector.gpconsultores.cl/api/muestras"

    cuerpo = {
        "programa": payload.programa,
        "estaciones": payload.estaciones
    }

    # Reenviar el header Authorization que envía Flutter (Basic o Bearer)
    headers = {"Content-Type": "application/json"}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    logger.info(f"📋 [ HISTORIAL MUESTRAS ] Reenviando a API externa. Programa: [ {payload.programa} ] | Estaciones: {payload.estaciones}")

    try:
        respuesta = req.post(URL_EXTERNA, json=cuerpo, headers=headers, timeout=30)

        if respuesta.status_code == 401:
            logger.error("🚨 API externa rechazó las credenciales (401 Unauthorized).")
            raise HTTPException(status_code=502, detail="La API externa rechazó las credenciales (401 Unauthorized).")

        respuesta.raise_for_status()
        datos = respuesta.json()

        # --- Normalización: siempre retornar una lista a Flutter ---
        if isinstance(datos, dict):
            logger.info(f"🔍 Respuesta externa es un dict. Llaves detectadas: {list(datos.keys())}")

        lista_muestras = []
        if isinstance(datos, list):
            lista_muestras = datos
        elif isinstance(datos, dict):
            # Buscar por llaves conocidas primero
            llaves_comunes = ["data", "muestras", "registros", "historico", "result", "items", "results"]
            for key in llaves_comunes:
                if key in datos and isinstance(datos[key], list):
                    lista_muestras = datos[key]
                    logger.info(f"✅ Lista extraída desde la llave: '{key}'")
                    break

            # Fallback agresivo: cualquier valor que sea lista
            if not lista_muestras:
                logger.warning(f"⚠️ Ninguna llave conocida contiene una lista. Intentando fallback agresivo...")
                for val in datos.values():
                    if isinstance(val, list):
                        lista_muestras = val
                        break

            if not lista_muestras:
                logger.warning(f"⚠️ No se pudo extraer una lista del dict externo. Llaves: {list(datos.keys())}")

        # Phase 72: Conversión UTM a WGS84 para el historial de muestras antes del dispatch
        for m in lista_muestras:
            if isinstance(m, dict) and m.get("latitud") and m.get("longitud"):
                # convert_utm_to_wgs84 detecta si ya son decimales y no los altera
                lat, lon = convert_utm_to_wgs84(easting=m["longitud"], northing=m["latitud"])
                m["latitud"] = lat
                m["longitud"] = lon
        
        logger.info(f"✅ Normalización y conversión de coordenadas completada. Registros enviados a Flutter: {len(lista_muestras)}")
        return lista_muestras

    except req.exceptions.Timeout:
        logger.error("🚨 Timeout al conectarse a la API externa de muestras.")
        raise HTTPException(status_code=504, detail="La API externa no respondió a tiempo.")

    except req.exceptions.RequestException as e:
        logger.error(f"🚨 Error de conexión con la API externa: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error al conectar con la API externa: {str(e)}")
