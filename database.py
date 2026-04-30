import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cargar variables desde el archivo .env
load_dotenv()

# Obtener la URL desde el entorno (Requerido en producción)
URL_BASE_DATOS = os.getenv("DATABASE_URL")
if not URL_BASE_DATOS:
    # Fallback para desarrollo local (sin credenciales sensibles por defecto)
    URL_BASE_DATOS = "mysql+pymysql://admin:password@localhost:3306/gpconsul_monitoreos"
    # O simplemente lanzar un error si es crítico
    # raise ValueError("DATABASE_URL no está definida en el archivo .env")

engine = create_engine(URL_BASE_DATOS, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
