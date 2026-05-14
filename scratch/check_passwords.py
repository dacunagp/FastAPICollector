from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import UsuarioDB
import os
from dotenv import load_dotenv

load_dotenv()

URL_BASE_DATOS = os.getenv("DATABASE_URL")
if not URL_BASE_DATOS:
    URL_BASE_DATOS = "mysql+pymysql://admin:password@localhost:3306/gpconsul_monitoreos"

def check_users():
    try:
        engine = create_engine(URL_BASE_DATOS)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("--- QUERYING USUARIOS ---")
        usuarios = db.query(UsuarioDB).all()
        
        for u in usuarios:
            print(f"ID: {u.id_usuario} | Nombre: {u.nombre} | Email: {u.email} | Clave App: {u.clave_app} | Password: {u.password}")
        
        print(f"\nTotal users in table: {len(usuarios)}")
        
        db.close()
    except Exception as e:
        print(f"Error during inspection: {e}")

if __name__ == "__main__":
    check_users()
