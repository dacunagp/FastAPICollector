import logging
import requests as req
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import MonitoreoDB, MonitoreoFotoDB, EstacionDB, MonitoreoDetalleDB
from schemas import SyncPayload, MuestrasPayload
from auth import verificar_credenciales
from utils import save_base64_image, save_dynamic_photo, convert_utm_to_wgs84

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
                
                # --- Fase 86: Limpiar Base64 original para prepararlo para la ruta ---
                existente.foto_path = None
                existente.foto_multiparametro = None
                existente.foto_turbiedad = None
                
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
                    # --- Fase 86: Iniciamos en None para guardar la ruta después ---
                    foto_path=None,
                    foto_multiparametro=None,
                    foto_turbiedad=None
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
