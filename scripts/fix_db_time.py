import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Añadir el directorio actual al path para importar database
sys.path.append(os.getcwd())

from database import URL_BASE_DATOS

def fix_timestamps():
    print(f"Connecting to: {URL_BASE_DATOS}")
    try:
        engine = create_engine(URL_BASE_DATOS)
        with engine.connect() as conn:
            print("Updating 'monitoreos' table...")
            conn.execute(text("""
                UPDATE monitoreos 
                SET created_at = DATE_ADD(created_at, INTERVAL 4 HOUR), 
                    updated_at = DATE_ADD(updated_at, INTERVAL 4 HOUR),
                    fecha_hora = DATE_ADD(fecha_hora, INTERVAL 4 HOUR)
            """))
            
            print("Updating 'audit_logs' table...")
            conn.execute(text("""
                UPDATE audit_logs 
                SET fecha_hora = DATE_ADD(fecha_hora, INTERVAL 4 HOUR)
            """))
            
            print("Updating 'monitoreo_fotos' table...")
            conn.execute(text("""
                UPDATE monitoreo_fotos 
                SET created_at = DATE_ADD(created_at, INTERVAL 4 HOUR), 
                    updated_at = DATE_ADD(updated_at, INTERVAL 4 HOUR)
            """))
            
            conn.commit()
            print("✅ Successfully adjusted existing timestamps by +4 hours.")
    except Exception as e:
        print(f"❌ Error adjusting timestamps: {e}")

if __name__ == "__main__":
    confirm = input("This will add 4 hours to ALL existing records in the database. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        fix_timestamps()
    else:
        print("Aborted.")
