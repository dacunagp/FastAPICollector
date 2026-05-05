from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import UsuarioDB
import os
from dotenv import load_dotenv

load_dotenv()
# We found that mysql+pymysql://root:@localhost:3306/gpconsul_monitoreos works
URL = "mysql+pymysql://root:@localhost:3306/gpconsul_monitoreos"

def check_data():
    try:
        engine = create_engine(URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        usuarios = db.query(UsuarioDB).all()
        print(f"Total users found: {len(usuarios)}")
        for u in usuarios:
            print(f"User: {u.nombre}, Email: {u.email}, Password: {u.password}")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
