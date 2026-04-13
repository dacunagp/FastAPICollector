import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import CampanaDB, EquipoDB, MatrizDB, MetodoDB, ParametroDB, UsuarioDB
from schemas import Campana, Equipo, Matriz, Metodo, Parametro, Usuario
from auth import verificar_credenciales
from utils import convert_utm_to_wgs84

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", dependencies=[Depends(verificar_credenciales)])

@router.get("/campanas", response_model=List[Campana])
def get_campanas(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ CAMPANAS ] solicitada. (Incluyendo Estaciones)")
    # Phase 122: Filtro para retornar solo campañas activas y asignadas a la App Móvil (collector == 1)
    campanas = db.query(CampanaDB).filter(CampanaDB.collector == 1, CampanaDB.disabled == 0).options(joinedload(CampanaDB.estaciones)).all()
    
    # Phase 72: Refactorización para conversión explícita en el router
    for campana in campanas:
        for estacion in campana.estaciones:
            # Convertimos las coordenadas UTM (Este/Norte) a WGS84 (Lon/Lat) para la App Móvil
            lat, lon = convert_utm_to_wgs84(easting=estacion.utm_este, northing=estacion.utm_norte)
            estacion.latitud = lat
            estacion.longitud = lon
            
    return campanas

@router.get("/equipos", response_model=List[Equipo])
def get_equipos(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ EQUIPOS ] solicitada.")
    return db.query(EquipoDB).all()

@router.get("/matriz_aguas", response_model=List[Matriz])
def get_matrices(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ MATRIZ_AGUAS ] solicitada.")
    return db.query(MatrizDB).all()

@router.get("/metodos", response_model=List[Metodo])
def get_metodos(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ METODOS ] solicitada.")
    return db.query(MetodoDB).all()

@router.get("/parametros", response_model=List[Parametro])
def get_parametros(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ PARAMETROS ] solicitada.")
    return db.query(ParametroDB).all()

@router.get("/usuarios", response_model=List[Usuario])
def get_usuarios(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ USUARIOS ] solicitada.")
    # Trae los usuarios sin exponer la contraseña
    return db.query(UsuarioDB).all()
