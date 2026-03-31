from pydantic import BaseModel
from typing import List, Optional

class Campana(BaseModel):
    id_campana: int
    nombre_campana: Optional[str] = None
    datawarehouse: Optional[int] = None
    collector: Optional[int] = None
    disabled: Optional[int] = None
    class Config: from_attributes = True

class Equipo(BaseModel):
    id_equipo: int
    id_app: Optional[int] = None
    codigo_equipo: Optional[str] = None
    nombre_parametro: Optional[str] = None
    id_form: Optional[int] = None
    class Config: from_attributes = True

class Matriz(BaseModel):
    id_matriz: int
    nombre_matriz: Optional[str] = None
    class Config: from_attributes = True

class Metodo(BaseModel):
    id_metodo: int
    metodo: Optional[str] = None
    class Config: from_attributes = True

class Parametro(BaseModel):
    id_parametro: int
    nombre_parametro: Optional[str] = None
    parametro_interno: Optional[str] = None
    unidad: Optional[str] = None
    enable: Optional[int] = None
    min: Optional[float] = None
    max: Optional[float] = None
    class Config: from_attributes = True

class Usuario(BaseModel):
    id_usuario: int
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    clave_app: Optional[str] = None
    email: Optional[str] = None
    habilitado: Optional[int] = None
    class Config: from_attributes = True

# --- Esquemas para POST ---
class MonitoreoItem(BaseModel):
    id: int
    device_id: str
    programa_id: Optional[int] = None
    estacion_id: Optional[int] = None
    fecha_hora: Optional[str] = None
    monitoreo_fallido: int = 0
    observacion: Optional[str] = None
    matriz_id: Optional[int] = None
    equipo_multi_id: Optional[int] = None
    turbidimetro_id: Optional[int] = None
    metodo_id: Optional[int] = None
    hidroquimico: int = 0
    isotopico: int = 0
    cod_laboratorio: Optional[str] = None
    usuario_id: Optional[int] = None
    is_draft: int = 0
    equipo_nivel_id: Optional[int] = None
    tipo_pozo: Optional[str] = None
    fecha_hora_nivel: Optional[str] = None
    temperatura: Optional[float] = None
    ph: Optional[float] = None
    conductividad: Optional[float] = None
    oxigeno: Optional[float] = None
    turbiedad: Optional[float] = None
    profundidad: Optional[float] = None
    nivel: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    foto_path: Optional[str] = None
    foto_multiparametro: Optional[str] = None
    foto_turbiedad: Optional[str] = None

class SyncPayload(BaseModel):
    monitoreos: List[MonitoreoItem]

class MuestrasPayload(BaseModel):
    programa: str
    estaciones: List[str]
