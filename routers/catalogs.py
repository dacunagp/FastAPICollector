from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import CampanaDB, EquipoDB, MatrizDB, MetodoDB, ParametroDB, UsuarioDB
from schemas import Campana, Equipo, Matriz, Metodo, Parametro, Usuario
from auth import verificar_credenciales

router = APIRouter(prefix="/api", dependencies=[Depends(verificar_credenciales)])

@router.get("/campanas", response_model=List[Campana])
def get_campanas(db: Session = Depends(get_db)):
    return db.query(CampanaDB).all()

@router.get("/equipos", response_model=List[Equipo])
def get_equipos(db: Session = Depends(get_db)):
    return db.query(EquipoDB).all()

@router.get("/matriz_aguas", response_model=List[Matriz])
def get_matrices(db: Session = Depends(get_db)):
    return db.query(MatrizDB).all()

@router.get("/metodos", response_model=List[Metodo])
def get_metodos(db: Session = Depends(get_db)):
    return db.query(MetodoDB).all()

@router.get("/parametros", response_model=List[Parametro])
def get_parametros(db: Session = Depends(get_db)):
    return db.query(ParametroDB).all()

@router.get("/usuarios", response_model=List[Usuario])
def get_usuarios(db: Session = Depends(get_db)):
    # Trae los usuarios sin exponer la contraseña
    return db.query(UsuarioDB).all()
