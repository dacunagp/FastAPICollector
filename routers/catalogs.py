import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import CampanaDB, EquipoDB, MatrizDB, MetodoDB, ParametroDB, UsuarioDB
from schemas import Campana, Equipo, Matriz, Metodo, Parametro, Usuario
from auth import verificar_credenciales

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", dependencies=[Depends(verificar_credenciales)])

@router.get("/campanas", response_model=List[Campana])
def get_campanas(db: Session = Depends(get_db)):
    logger.info("📋 Consulta de catálogo [ CAMPANAS ] solicitada. (Incluyendo Estaciones)")
    # Se eliminó cualquier filtro de 'disabled == 0' para mostrar todo el catálogo
    # Importante usar joinedload para que las estaciones se incluyan en el JSON de respuesta
    return db.query(CampanaDB).options(joinedload(CampanaDB.estaciones)).all()

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
