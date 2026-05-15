import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import MonitoreoDB
from datetime import datetime

URL_BASE_DATOS = "mysql+pymysql://admin:password@localhost:3306/gpconsul_monitoreos"

def check_data():
    engine = create_engine(URL_BASE_DATOS)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    last_record = db.query(MonitoreoDB).order_by(MonitoreoDB.id.desc()).first()
    if last_record:
        print(f"ID: {last_record.id}")
        print(f"created_at: {last_record.created_at}")
        print(f"Current local time: {datetime.now()}")
    else:
        print("No records found in monitoreos.")
    
    db.close()

if __name__ == "__main__":
    check_data()
