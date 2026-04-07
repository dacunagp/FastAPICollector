from database import engine
from sqlalchemy import text

if __name__ == "__main__":
    print("🚀 Modificando 'parameter_id' para aceptar NULL...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE monitoreo_detalles MODIFY COLUMN parameter_id varchar(255) NULL;"))
            print("✅ 'parameter_id' modificado correctamente.")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE monitoreo_detalles MODIFY COLUMN updated_at timestamp NULL;"))
            conn.execute(text("ALTER TABLE monitoreo_detalles MODIFY COLUMN created_at timestamp NULL;"))
            print("✅ timestamps modificados correctamente.")
        except Exception as e:
            pass
            
        conn.commit()
