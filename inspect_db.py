from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ParametroDB
import json
import logging

# Connection string
URL_BASE_DATOS = "mysql+pymysql://root:1234@localhost:3306/gpconsul_monitoreos"

def inspect():
    try:
        engine = create_engine(URL_BASE_DATOS)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("--- QUERYING PARAMETERS ---")
        parametros = db.query(ParametroDB).all()
        
        profundidad_found = False
        for p in parametros:
            p_data = {
                "id_parametro": p.id_parametro,
                "nombre_parametro": p.nombre_parametro,
                "parametro_interno": p.parametro_interno,
                "unidad": p.unidad,
                "enable": p.enable,
                "min": p.min,
                "max": p.max,
                "categoria": p.categoria
            }
            if "profundidad" in str(p.nombre_parametro).lower() or "profundidad" in str(p.parametro_interno).lower():
                print(f"✅ FOUND: {json.dumps(p_data, indent=2)}")
                profundidad_found = True
            else:
                # Optional: print summary for others
                pass
        
        if not profundidad_found:
            print("❌ 'Profundidad' NOT FOUND in the 'parametros' table.")
            
        print(f"\nTotal parameters in table: {len(parametros)}")
        
        db.close()
    except Exception as e:
        print(f"Error during inspection: {e}")

if __name__ == "__main__":
    inspect()
