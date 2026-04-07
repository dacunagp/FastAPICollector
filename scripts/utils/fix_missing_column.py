from sqlalchemy import text
from database import engine

def migrate_missing_column():
    print("🚀 Iniciando migración manual: Agregando columna 'parametro' a 'monitoreo_detalles'...")
    
    # Sentencia SQL para alterar la tabla
    # Agregamos 'parametro' después de 'monitoreo_id' para mantener el orden lógico
    sql = text("ALTER TABLE monitoreo_detalles ADD COLUMN parametro VARCHAR(255) AFTER monitoreo_id;")
    
    try:
        with engine.connect() as conn:
            # Ejecutar la alteración
            conn.execute(sql)
            conn.commit()
            print("✅ Columna 'parametro' agregada exitosamente a la tabla 'monitoreo_detalles'.")
            
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("⚠️ La columna 'parametro' ya existe en la base de datos.")
        else:
            print(f"🚨 Error crítico durante la migración: {str(e)}")

if __name__ == "__main__":
    migrate_missing_column()
