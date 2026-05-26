import logging
import json
import os
import base64
from typing import Optional
import requests as req
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import MonitoreoDB, MonitoreoFotoDB, EstacionDB, MonitoreoDetalleDB
from schemas import SyncPayload, MuestrasPayload
from auth import verificar_credenciales
from utils import save_dynamic_photo, convert_utm_to_wgs84, log_audit, get_chile_time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", dependencies=[Depends(verificar_credenciales)])

@router.post("/sync/monitoreos")
async def sync_monitoreos(
    payload: str = Form(...), 
    firma_operador: Optional[UploadFile] = File(None), 
    foto_path: Optional[UploadFile] = File(None),
    foto_multiparametro: Optional[UploadFile] = File(None),
    foto_turbiedad: Optional[UploadFile] = File(None),
    foto_caudal: Optional[UploadFile] = File(None),
    foto_nivel_freatico: Optional[UploadFile] = File(None),
    foto_muestreo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """ Recibe array de monitoreos del dispositivo móvil (multipart) y los guarda con manejo de errores """
    # Parsear el payload JSON desde el campo Form
    try:
        data_dict = json.loads(payload)
        payload_obj = SyncPayload(**data_dict)
    except Exception as e:
        logger.error(f"❌ Error al parsear payload JSON: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error en formato JSON del payload: {str(e)}")

    contador_nuevos = 0
    contador_editados = 0
    ids_registrados = []  # ✅ Lista para rastrear mapeo de IDs locales vs servidor
    
    # Log: Inicio de sincronización (Narrativo)
    dispositivo = payload_obj.monitoreos[0].device_id if payload_obj.monitoreos else "DESCONOCIDO"
    logger.info(f"🔄 Iniciando sincronización de registros para el dispositivo: [ {dispositivo} ]")
    
    # Guardar firma si existe (se aplica a los registros del lote)
    firma_path_guardada = None
    firma_bytes = None
    if firma_operador:
        logger.info(f"✍️ Recibida firma del operador: {firma_operador.filename}")
        try:
            # Leer contenido del archivo
            firma_bytes = await firma_operador.read()
        except Exception as e:
            logger.error(f"❌ Error al leer firma_operador: {str(e)}")

    # Procesar fotos de evidencia recibidas vía Multipart (Fase Multipart Evidence)
    multipart_photos_data = {} # Guardaremos dict con bytes y content_type
    evidence_fields = {
        "general": foto_path,
        "multiparametro": foto_multiparametro,
        "turbiedad": foto_turbiedad,
        "caudal": foto_caudal,
        "nivel_freatico": foto_nivel_freatico,
        "muestreo": foto_muestreo
    }
    
    for key, file_obj in evidence_fields.items():
        if file_obj:
            logger.info(f"📸 Recibida foto multipart [ {key} ]: {file_obj.filename}")
            try:
                multipart_photos_data[key] = {
                    "bytes": await file_obj.read(),
                    "content_type": file_obj.content_type or "image/jpeg"
                }
            except Exception as e:
                logger.error(f"❌ Error al leer foto multipart {key}: {str(e)}")

    # Diccionario para rastrear rutas ya guardadas en este lote (Batch-wide optimization)
    rutas_guardadas_lote = {}

    try:
        for item in payload_obj.monitoreos:
            # Fase 132: Validación temprana — id_local es requerido por la BD
            if item.id_local is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"El campo 'id' o 'id_local' es requerido para device_id='{item.device_id}'. La base de datos no acepta id_local=NULL."
                )
            logger.info(f"📍 Procesando registro móvil [ ID Local: {item.id_local} ]...")
            
            # 1. Conversión de fechas con validación de "vacio" para evitar copias accidentales
            # La fecha_hora principal tomará la fecha de subida del monitoreo al servidor
            fh = get_chile_time()
                
            fh_nivel = None
            if item.fecha_hora_nivel and str(item.fecha_hora_nivel).strip() != "":
                try:
                    fh_nivel = datetime.strptime(item.fecha_hora_nivel, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Formato de fecha_hora_nivel inválido: {item.fecha_hora_nivel}")
                    
            fh_caudal = None
            if item.fecha_hora_caudal and str(item.fecha_hora_caudal).strip() != "":
                try:
                    fh_caudal = datetime.strptime(item.fecha_hora_caudal, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Formato de fecha_hora_caudal inválido: {item.fecha_hora_caudal}")

            # --- CORRECCIÓN FECHA MUESTREO (Independiente) ---
            fh_muestreo = None
            if item.fecha_hora_muestreo and str(item.fecha_hora_muestreo).strip() != "":
                try:
                    fh_muestreo = datetime.strptime(item.fecha_hora_muestreo, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"⚠️ Formato inválido en muestreo para ID {item.id_local}")

            # 1.5 Depuración de fotos y campos recibidos
            logger.debug(f"🔍 [DEBUG SYNC] Datos recibidos para ID Local {item.id_local}: {item.model_dump(exclude={'foto_path', 'foto_multiparametro', 'foto_turbiedad', 'foto_caudal', 'foto_nivel_freatico', 'foto_muestreo', 'firma_path'})}")
            
            # Fase 170: Deep Debug - Se asegura que NINGÚN ID primario del móvil sea usado.
            item_data = item.model_dump()
            item_data.pop("id", None)
            
            logger.info(f"✨ Registro [ ID Local: {item.id_local} ] - Creando registro independiente en BD...")
            
            monitoreo_actual = MonitoreoDB(
                device_id=item.device_id,
                id_local=item.id_local, 
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
                tipo_nivel=item.tipo_nivel,
                fecha_hora_nivel=fh_nivel,
                equipo_caudal=item.equipo_caudal,
                nivel_caudal=item.nivel_caudal,
                fecha_hora_caudal=fh_caudal,
                turbiedad=item.turbiedad,
                profundidad=item.profundidad,
                nivel=item.nivel,
                latitud=item.latitud,
                longitud=item.longitud,
                detalles_json=json.dumps([d.model_dump() for d in item.detalles_json]) if isinstance(item.detalles_json, list) else item.detalles_json,
                multiparametros_json=json.dumps([d.model_dump() for d in item.multiparametros_json]) if isinstance(item.multiparametros_json, list) else item.multiparametros_json,
                foto_path=item.foto_path,
                foto_multiparametro=item.foto_multiparametro,
                foto_turbiedad=item.foto_turbiedad,
                foto_caudal=item.foto_caudal,
                foto_nivel_freatico=item.foto_nivel_freatico,
                foto_muestreo=item.foto_muestreo,
                fecha_hora_muestreo=fh_muestreo, # ✅ AHORA ES INDEPENDIENTE
                firma_path=item.firma_path,
                trazabilidad=json.dumps([t if isinstance(t, dict) else dict(t) for t in item.trazabilidad]) if getattr(item, "trazabilidad", None) else None
            )
            db.add(monitoreo_actual)
            contador_nuevos += 1
            
            # --- FASE 120: Almacenamiento Dinámico en Disco ---
            db.flush() 
            db_monitoreo_id = monitoreo_actual.id
            
            # ✅ Almacenamos el mapeo de ID Local del móvil vs ID Real que le dio MySQL
            ids_registrados.append({
                "id_local": item.id_local,
                "id_unica": db_monitoreo_id
            })
            fecha_base = fh if fh else get_chile_time()

            if getattr(item, "trazabilidad", None) and len(item.trazabilidad) > 0:
                logger.info(f"💾 Procesando {len(item.trazabilidad)} logs de trazabilidad desde la App...")
                
                # --- Fase: Consolidación de Auditoría ---
                # Agrupamos cambios por acción y referencia (ej: 'update' sobre la misma estación)
                # para evitar que aparezcan filas separadas por cada campo modificado.
                logs_agrupados = {}
                
                for log_local in item.trazabilidad:
                    try:
                        accion_raw = log_local.get("accion", "update")
                        ref_raw = log_local.get("registro_ref", "N/A")
                        # Usamos una clave única por acción y referencia dentro de este monitoreo
                        key = f"{accion_raw}_{ref_raw}"
                        
                        if key not in logs_agrupados:
                            logs_agrupados[key] = {
                                "accion": accion_raw,
                                "registro_ref": ref_raw,
                                "usuario_nombre": log_local.get("usuario_nombre"),
                                "created_at": log_local.get("created_at"),
                                "cambios_dict": {}
                            }
                        
                        # Extraer y fusionar el contenido de 'cambios' (JSON o Dict)
                        cambios_raw = log_local.get("cambios")
                        if cambios_raw:
                            if isinstance(cambios_raw, str):
                                try:
                                    # Si es una cadena JSON (común desde Flutter), la parseamos
                                    data = json.loads(cambios_raw)
                                    if isinstance(data, dict):
                                        logs_agrupados[key]["cambios_dict"].update(data)
                                    else:
                                        # Fallback si no es un dict: guardarlo como nota
                                        logs_agrupados[key]["cambios_dict"][f"nota_{len(logs_agrupados[key]['cambios_dict'])}"] = data
                                except json.JSONDecodeError:
                                    # Si no es JSON válido, guardar como texto plano
                                    logs_agrupados[key]["cambios_dict"][f"info_{len(logs_agrupados[key]['cambios_dict'])}"] = cambios_raw
                            elif isinstance(cambios_raw, dict):
                                # Si ya viene como diccionario, fusionar directamente
                                logs_agrupados[key]["cambios_dict"].update(cambios_raw)

                    except Exception as e:
                        logger.error(f"⚠️ Error al agrupar log local en {item.id_local}: {str(e)}")

                # Una vez agrupados, guardamos un solo registro por cada acción/referencia
                for log in logs_agrupados.values():
                    # Parsear la fecha original si existe
                    f_creado = None
                    if log["created_at"]:
                        try:
                            f_creado = datetime.fromisoformat(log["created_at"].replace('Z', '+00:00'))
                        except: pass

                    log_audit(
                        db=db, 
                        usuario_id=item.usuario_id, 
                        usuario_nombre=log["usuario_nombre"],
                        accion=log["accion"], 
                        tabla="App_collector", 
                        registro_id=db_monitoreo_id, 
                        detalles=log["cambios_dict"], # log_audit se encarga de convertir el dict a JSON
                        registro_ref=str(db_monitoreo_id),
                        created_at=f_creado
                    )


            station_name = "sin_estacion"
            if item.estacion_id:
                estacion_obj = db.query(EstacionDB).filter(EstacionDB.id_estacion == item.estacion_id).first()
                if estacion_obj and estacion_obj.estacion:
                    station_name = estacion_obj.estacion

            # Mapeo de fotos para procesar (incluyendo firma para consistencia)
            fotos_a_procesar = {
                'general': item.foto_path,
                'multiparametro': item.foto_multiparametro,
                'turbiedad': item.foto_turbiedad,
                'caudal': item.foto_caudal,
                'nivel_freatico': item.foto_nivel_freatico,
                'muestreo': item.foto_muestreo,
                'firma': item.firma_path
            }

            # Prioridad 1: Firma Multipart (Batch-wide)
            if firma_operador and not rutas_guardadas_lote.get('firma'):
                logger.info(f"✍️ Procesando firma multipart para el lote...")
                ruta_firma = save_dynamic_photo(
                    firma_bytes, 
                    fecha_base, 
                    db_monitoreo_id, 
                    "firma", 
                    station_name,
                    id_equipo=str(item.equipo_multi_id or 0),
                    content_type=firma_operador.content_type or "image/png"
                )
                if ruta_firma:
                    rutas_guardadas_lote['firma'] = ruta_firma

            for tipo, b64_json in fotos_a_procesar.items():
                ruta_final = None
                
                # Caso A: Existe un archivo Multipart para este tipo (Prioridad)
                if tipo in multipart_photos_data or (tipo == 'firma' and 'firma' in rutas_guardadas_lote):
                    # Si ya lo guardamos en este lote, usamos la misma ruta (Optimization)
                    if tipo in rutas_guardadas_lote:
                        ruta_final = rutas_guardadas_lote[tipo]
                    elif tipo in multipart_photos_data:
                        # Guardar por primera vez en este lote
                        photo_info = multipart_photos_data[tipo]
                        ruta_final = save_dynamic_photo(
                            photo_info["bytes"], 
                            fecha_base, 
                            db_monitoreo_id, 
                            tipo, 
                            station_name,
                            id_equipo=str(item.equipo_multi_id or 0),
                            content_type=photo_info["content_type"]
                        )
                        if ruta_final:
                            rutas_guardadas_lote[tipo] = ruta_final
                
                # Caso B: No hay multipart, pero hay Base64 en el JSON
                elif b64_json and len(b64_json) > 50:
                    logger.debug(f"📄 Procesando foto Base64 del JSON para tipo: {tipo} [ID Local: {item.id_local}]")
                    ruta_final = save_dynamic_photo(
                        b64_json, 
                        fecha_base, 
                        db_monitoreo_id, 
                        tipo, 
                        station_name,
                        id_equipo=str(item.equipo_multi_id or 0),
                        content_type="image/jpeg"
                    )

                # Si logramos obtener la URL de S3, actualizamos el modelo
                if ruta_final:
                    logger.info(f"✅ Foto/Firma subida: {ruta_final} [Tipo: {tipo}]")
                    if tipo == 'general': monitoreo_actual.foto_path = ruta_final
                    elif tipo == 'multiparametro': monitoreo_actual.foto_multiparametro = ruta_final
                    elif tipo == 'turbiedad': monitoreo_actual.foto_turbiedad = ruta_final
                    elif tipo == 'caudal': monitoreo_actual.foto_caudal = ruta_final
                    elif tipo == 'nivel_freatico': monitoreo_actual.foto_nivel_freatico = ruta_final
                    elif tipo == 'muestreo': monitoreo_actual.foto_muestreo = ruta_final
                    elif tipo == 'firma': monitoreo_actual.firma_path = ruta_final

                    # Mantener soporte legacy en tabla monitoreo_fotos
                    foto_existente = db.query(MonitoreoFotoDB).filter(
                        MonitoreoFotoDB.monitoreo_id == db_monitoreo_id,
                        MonitoreoFotoDB.tipo == tipo
                    ).first()
                    
                    if foto_existente:
                        foto_existente.ruta = ruta_final
                    else:
                        db.add(MonitoreoFotoDB(monitoreo_id=db_monitoreo_id, tipo=tipo, ruta=ruta_final))
            
            # --- NUEVA LÓGICA DE DETALLES/PARÁMETROS EXTRA (Fase 86) ---
            if item.detalles:
                logger.info(f"💾 Guardando {len(item.detalles)} parámetros extra (detalles) para el monitoreo...")
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
        logger.info(f"🚀 Sincronización Finalizada de forma exitosa. Se detectaron {contador_nuevos} nuevos registros.")
        

        return {
            "status": "success",
            "mensaje": f"Se sincronizaron con éxito {contador_nuevos} nuevos registros.",
            "ids_registrados": ids_registrados  # ✅ Enviamos el mapeo de IDs de vuelta a la App
        }

    except HTTPException:
        # Fase 132: Re-lanzar HTTPException (400, 422, etc.) sin envolverla en un 500
        db.rollback()
        raise

    except Exception as e:
        db.rollback() 
        logger.exception(f"🚨 ERROR CRÍTICO EN SYNC: {str(e)}") 
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno en el servidor/DB (Consulta el log de la API)"
        )

@router.post("/muestras")
def exponer_muestras(payload: MuestrasPayload, request: Request, db: Session = Depends(get_db)):
    """ Proxy hacia la API externa: reenvía la consulta de historial de muestras con autenticación """
    URL_EXTERNA = os.getenv("EXTERNAL_API_URL", "http://apicollector.gpconsultores.cl/api/muestras")

    cuerpo = {
        "programa": str(payload.programa),   # Fix: usar el programa real enviado por Flutter
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
                val = datos.get(key)
                if isinstance(val, list):
                    lista_muestras = val
                    logger.info(f"✅ Lista extraída desde la llave: '{key}'")
                    break
                elif val is not None and not isinstance(val, list):
                    logger.warning(f"⚠️ La llave '{key}' existe pero no contiene una lista. Tipo: {type(val).__name__}, Valor: {str(val)[:100]}")

            # Fallback agresivo: cualquier valor que sea lista
            if not lista_muestras:
                logger.warning(f"⚠️ Ninguna llave conocida contiene una lista. Intentando fallback agresivo...")
                for val in datos.values():
                    if isinstance(val, list):
                        lista_muestras = val
                        break

            if not lista_muestras:
                logger.warning(f"⚠️ No se pudo extraer una lista del dict externo. Llaves: {list(datos.keys())}")
                if "message" in datos:
                    logger.warning(f"💬 Mensaje de la API externa: {datos['message']}")

        # Phase 72: Conversión UTM a WGS84 para el historial de muestras antes del dispatch
        for m in lista_muestras:
            if isinstance(m, dict):
                lat_raw = m.get("latitud")
                lon_raw = m.get("longitud")
                if lat_raw is not None and lon_raw is not None:
                    try:
                        # Asegurar que son numéricos antes de la conversión
                        lat_val = float(lat_raw)
                        lon_val = float(lon_raw)
                        lat, lon = convert_utm_to_wgs84(easting=lon_val, northing=lat_val)
                        m["latitud"] = lat
                        m["longitud"] = lon
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Coordenadas inválidas en muestra: lat={lat_raw}, lon={lon_raw}")
        
        # --- Fase 140: Integración de registros locales (Historial Local) ---
        try:
            # Buscar registros en la BD local que coincidan con el programa y estaciones
            # Nota: estaciones en el payload es List[str], en la BD estacion_id es int
            estaciones_ids = []
            for e_id in payload.estaciones:
                try: estaciones_ids.append(int(e_id))
                except: continue

            if estaciones_ids:
                logger.info(f"🏠 Buscando registros locales para el historial. Programa: {payload.programa}, Estaciones: {estaciones_ids}")
                registros_locales = db.query(MonitoreoDB).filter(
                    MonitoreoDB.programa_id == payload.programa,
                    MonitoreoDB.estacion_id.in_(estaciones_ids)
                ).order_by(MonitoreoDB.fecha_hora.desc()).all()

                for r in registros_locales:
                    # Evitar duplicados si ya vienen de la API externa (comparando por fecha y estación o id_local)
                    # Por simplicidad, agregamos los que no estén en la lista por 'fecha_hora' y 'estacion_id'
                    ya_existe = any(
                        str(m.get("fecha_hora")) == (r.fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_hora else None) and 
                        str(m.get("estacion_id")) == str(r.estacion_id)
                        for m in lista_muestras
                    )
                    
                    if not ya_existe:
                        m_local = {
                            "id": r.id,
                            "id_local": r.id_local,
                            "device_id": r.device_id,
                            "fecha_hora": r.fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_hora else None,
                            "fecha_hora_muestreo": r.fecha_hora_muestreo.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_hora_muestreo else None,
                            "estacion_id": r.estacion_id,
                            "matriz_id": r.matriz_id,
                            "tipo_pozo": r.tipo_pozo,
                            "tipo_nivel": r.tipo_nivel,
                            "turbiedad": r.turbiedad,
                            "nivel": r.nivel,
                            "latitud": r.latitud,
                            "longitud": r.longitud,
                            "observacion": r.observacion,
                            "is_local": True # Flag para identificar que viene del collector
                        }
                        lista_muestras.insert(0, m_local) # Insertar al inicio para que aparezcan primero
                
                logger.info(f"✅ Historial mezclado. Total registros: {len(lista_muestras)} ({len(registros_locales)} locales)")

        except Exception as e:
            logger.error(f"⚠️ Error al mezclar registros locales: {str(e)}")
        
        logger.info(f"✅ Normalización y conversión de coordenadas completada. Registros enviados a Flutter: {len(lista_muestras)}")
        return lista_muestras

    except req.exceptions.Timeout:
        logger.error("🚨 Timeout al conectarse a la API externa de muestras.")
        raise HTTPException(status_code=504, detail="La API externa no respondió a tiempo.")

    except req.exceptions.RequestException as e:
        logger.error(f"🚨 Error de conexión con la API externa: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error al conectar con la API externa: {str(e)}")