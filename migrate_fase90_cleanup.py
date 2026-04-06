"""
Fase 90 — Limpieza: Eliminar columnas obsoletas de monitoreo_detalles
Ejecutar UNA SOLA VEZ para limpiar el esquema.
    python migrate_fase90_cleanup.py
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🚀 Fase 90 — Iniciando limpieza de monitoreo_detalles...")

    columns_to_drop = ["parameter_id", "value", "created_at", "updated_at"]

    with engine.connect() as conn:
        for column in columns_to_drop:
            try:
                print(f"  Wait... intentando eliminar columna '{column}'...")
                conn.execute(text(
                    f"ALTER TABLE monitoreo_detalles DROP COLUMN {column};"
                ))
                print(f"  ✅  Columna '{column}' eliminada exitosamente.")
            except Exception as e:
                if "check that column/key exists" in str(e).lower() or "1091" in str(e):
                    print(f"  ℹ️  La columna '{column}' no existe o ya fue eliminada.")
                else:
                    print(f"  ⚠️  Error al eliminar '{column}': {e}")

        conn.commit()

    print("🏁 Limpieza Fase 90 completada exitosamente.")

if __name__ == "__main__":
    migrate()
