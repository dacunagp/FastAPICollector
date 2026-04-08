from pydantic import BaseModel, model_validator
from typing import List, Optional, Any
from utils import convert_utm_to_wgs84

class Campana(BaseModel):
    id_campana: int
    nombre_campana: Optional[str] = None
    datawarehouse: Optional[int] = None
    collector: Optional[int] = None
    disabled: Optional[int] = None
    estaciones: List['Estacion'] = [] # Soporte para estaciones anidadas
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
    categoria: Optional[str] = 'adicional'
    class Config: from_attributes = True

class Usuario(BaseModel):
    id_usuario: int
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    clave_app: Optional[str] = None
    email: Optional[str] = None
    habilitado: Optional[int] = None
    class Config: from_attributes = True

class Estacion(BaseModel):
    id_estacion: int
    estacion: Optional[str] = None
    utm_este: Optional[float] = None
    utm_norte: Optional[float] = None
    
    # Campos de compatibilidad para la App Móvil
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    @model_validator(mode='after')
    def set_compat_coords(self) -> 'Estacion':
        # Si tenemos coordenadas UTM, las convertimos a WGS84 para la App Móvil
        if self.utm_norte and self.utm_este:
            lat, lon = convert_utm_to_wgs84(easting=self.utm_este, northing=self.utm_norte)
            self.latitud = lat
            self.longitud = lon
        else:
            # Fallback por si no hay UTM pero hay campos de latitud/longitud
            if self.latitud is None: self.latitud = self.utm_norte
            if self.longitud is None: self.longitud = self.utm_este
        return self

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
    
    # Fase 108: Pivot a Document Pattern (JSON)
    detalles_json: Optional[Any] = None
    
    # Fase 113: Backend Support for Dual JSON Architecture
    multiparametros_json: Optional[Any] = None
    
    # Campo para parámetros dinámicos (Fase 86 - Legacy support)
    detalles: List['DetalleSync'] = []

class SyncPayload(BaseModel):
    monitoreos: List[MonitoreoItem]

class DetalleSync(BaseModel):
    """ Esquema para los parámetros dinámicos extra (Fase 86 → Fase 88: valor dinámico) """
    parametro: str
    valor: Any                           # Fase 88: acepta number, string, boolean desde el móvil
    tipo_dato: Optional[str] = None      # Fase 88: "number", "text", "boolean" — autodetectado si no se envía

    @model_validator(mode='after')
    def coerce_valor_and_detect_type(self) -> 'DetalleSync':
        """ Convierte valor a string y auto-detecta tipo_dato si el móvil no lo envió """
        raw = self.valor
        if self.tipo_dato is None:
            if isinstance(raw, bool):
                self.tipo_dato = "boolean"
            elif isinstance(raw, (int, float)):
                self.tipo_dato = "number"
            else:
                self.tipo_dato = "text"
        self.valor = str(raw)
        return self

    class Config: from_attributes = True

class MuestrasPayload(BaseModel):
    programa: str
    estaciones: List[str]

# --- Fase 97: Esquemas para Analítica ---
class AnalyticsPoint(BaseModel):
    valor: float
    fecha: Optional[str] = None
    estacion: Optional[str] = None
    is_outlier: bool = False
    is_test: bool = False

class AnalyticsResponse(BaseModel):
    parametro: str
    media: float
    desviacion_estandar: float
    puntos: List[AnalyticsPoint]
    count_total: int
    count_clean: int
    count_outliers: int
