from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ¡OJO! Cambia 'TU_CONTRASEÑA_AQUI' por tu clave real de MySQL si la cambias.
URL_BASE_DATOS = "mysql+pymysql://root:1234@localhost:3306/gpconsul_monitoreos"

engine = create_engine(URL_BASE_DATOS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
