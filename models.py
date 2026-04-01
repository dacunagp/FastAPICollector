from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from database import Base

class CampanaDB(Base):
    __tablename__ = "campanas"
    id_campana = Column(Integer, primary_key=True, index=True)
    nombre_campana = Column(String(50))
    datawarehouse = Column(Integer)
    collector = Column(Integer)
    disabled = Column(Integer)
    
    # Relación con estaciones a través de campana_estacion
    estaciones = relationship("EstacionDB", secondary="campana_estacion", back_populates="campanas")

class EquipoDB(Base):
    __tablename__ = "equipos"
    id_equipo = Column(Integer, primary_key=True, index=True)
    id_app = Column(Integer)
    codigo_equipo = Column(String(50))
    nombre_parametro = Column(String(50))
    id_form = Column(Integer)

class MatrizDB(Base):
    __tablename__ = "matriz_aguas"
    id_matriz = Column(Integer, primary_key=True, index=True)
    nombre_matriz = Column(String(100))

class MetodoDB(Base):
    __tablename__ = "metodos"
    id_metodo = Column(Integer, primary_key=True, index=True)
    metodo = Column(String(50))

class ParametroDB(Base):
    __tablename__ = "parametros"
    id_parametro = Column(Integer, primary_key=True, index=True)
    nombre_parametro = Column(String(255))
    parametro_interno = Column(String(255))
    unidad = Column(String(255))
    enable = Column(Integer)
    min = Column(Float)
    max = Column(Float)

class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50))
    apellido = Column(String(50))
    clave_app = Column(String(50))
    email = Column(String(50))
    habilitado = Column(Integer)

class MonitoreoDB(Base):
    __tablename__ = "monitoreos"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255))
    id_local = Column(Integer)
    programa_id = Column(Integer)
    estacion_id = Column(Integer)
    fecha_hora = Column(DateTime)
    monitoreo_fallido = Column(Integer)
    observacion = Column(Text)
    matriz_id = Column(Integer)
    equipo_multi_id = Column(Integer)
    turbidimetro_id = Column(Integer)
    metodo_id = Column(Integer)
    hidroquimico = Column(Integer)
    isotopico = Column(Integer)
    cod_laboratorio = Column(String(255))
    usuario_id = Column(Integer)
    is_draft = Column(Integer)
    equipo_nivel_id = Column(Integer)
    tipo_pozo = Column(String(255))
    fecha_hora_nivel = Column(DateTime)
    temperatura = Column(Float)
    ph = Column(Float)
    conductividad = Column(Float)
    oxigeno = Column(Float)
    turbiedad = Column(Float)
    profundidad = Column(Float)
    nivel = Column(Float)
    latitud = Column(Float)
    longitud = Column(Float)
    foto_path = Column(LONGTEXT)
    foto_multiparametro = Column(LONGTEXT)
    foto_turbiedad = Column(LONGTEXT)

class MonitoreoFotoDB(Base):
    __tablename__ = "monitoreo_fotos"
    id = Column(Integer, primary_key=True, index=True)
    monitoreo_id = Column(Integer, index=True)
    tipo = Column(String(50)) # 'general', 'multiparametro', 'turbiedad'
    ruta = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EstacionDB(Base):
    __tablename__ = "estaciones"
    id_estacion = Column(Integer, primary_key=True, index=True)
    estacion = Column(String(50))
    utm_este = Column(Float)
    utm_norte = Column(Float)
    
    campanas = relationship("CampanaDB", secondary="campana_estacion", back_populates="estaciones")

class CampanaEstacionDB(Base):
    __tablename__ = "campana_estacion"
    id_camp_est = Column(Integer, primary_key=True, index=True)
    id_campana = Column(Integer, ForeignKey("campanas.id_campana"))
    id_estacion = Column(Integer, ForeignKey("estaciones.id_estacion"))
