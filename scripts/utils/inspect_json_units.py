from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import MonitoreoDB
import json

# Connection string
URL_BASE_DATOS = "mysql+pymysql://admin:gp2026@localhost:3306/gpconsul_monitoreos"

def inspect_monitoreo():
    try:
        engine = create_engine(URL_BASE_DATOS)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("--- QUERYING MONITOREO UNIT-TESTER-125 ---")
        monitoreo = db.query(MonitoreoDB).filter(
            MonitoreoDB.device_id == "UNIT-TESTER-125",
            MonitoreoDB.id_local == 9999
        ).first()
        
        if monitoreo:
            print(f"✅ Found Monitoreo ID: {monitoreo.id}")
            print(f"detalles_json: {monitoreo.detalles_json}")
            print(f"multiparametros_json: {monitoreo.multiparametros_json}")
            
            # Intentar parsear para verificar que es JSON válido y tiene las unidades
            detalles = json.loads(monitoreo.detalles_json) if monitoreo.detalles_json else []
            multi = json.loads(monitoreo.multiparametros_json) if monitoreo.multiparametros_json else []
            
            print("\nParsed detalles_json:")
            for item in detalles:
                print(f" - {item.get('parametro')}: {item.get('valor')} [{item.get('unidad')}]")
                
            print("\nParsed multiparametros_json:")
            for item in multi:
                print(f" - {item.get('parametro')}: {item.get('valor')} [{item.get('unidad')}]")
        else:
            print("❌ Monitoreo NOT FOUND.")
            
        db.close()
    except Exception as e:
        print(f"Error during inspection: {e}")

if __name__ == "__main__":
    inspect_monitoreo()
