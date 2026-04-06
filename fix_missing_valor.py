from sqlalchemy import text
from database import engine

def migrate_missing_valor():
    print("🚀 Iniciando migración manual: Agregando columna 'valor' a 'monitoreo_detalles'...")
    
    # Sentencia SQL para alterar la tabla
    # Agregamos 'valor' después de 'parametro'
    sql = text("ALTER TABLE monitoreo_detalles ADD COLUMN valor FLOAT AFTER parametro;")
    
    try:
        with engine.connect() as conn:
            # Ejecutar la alteración
            conn.execute(sql)
            conn.commit()
            print("✅ Columna 'valor' agregada exitosamente a la tabla 'monitoreo_detalles'.")
            
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("⚠️ La columna 'valor' ya existe en la base de datos.")
        else:
            print(f"🚨 Error crítico durante la migración: {str(e)}")

if __name__ == "__main__":
    migrate_missing_valor()
