"""
Fase 88 — Migración: monitoreo_detalles.valor -> String + nueva columna tipo_dato
Ejecutar UNA SOLA VEZ antes de reiniciar la API.
    python migrate_fase88_valor_to_string.py
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🚀 Fase 88 — Iniciando migración de monitoreo_detalles...")

    with engine.connect() as conn:
        # 1. Cambiar 'valor' de FLOAT a VARCHAR(255), convirtiendo datos existentes
        try:
            conn.execute(text(
                "ALTER TABLE monitoreo_detalles MODIFY COLUMN valor VARCHAR(255);"
            ))
            print("  ✅  Columna 'valor' convertida de FLOAT a VARCHAR(255).")
        except Exception as e:
            if "Unknown column" in str(e):
                print(f"  ⚠️  Columna 'valor' no existe todavía, se creará con el modelo. ({e})")
            else:
                print(f"  ⚠️  Posible error al modificar 'valor': {e}")

        # 2. Agregar nueva columna 'tipo_dato'
        try:
            conn.execute(text(
                "ALTER TABLE monitoreo_detalles ADD COLUMN tipo_dato VARCHAR(50) AFTER valor;"
            ))
            print("  ✅  Columna 'tipo_dato' agregada exitosamente.")
        except Exception as e:
            if "Duplicate column" in str(e):
                print(f"  ℹ️  La columna 'tipo_dato' ya existe, omitiendo. ({e})")
            else:
                print(f"  ⚠️  Posible error al agregar 'tipo_dato': {e}")

        # 3. Backfill: marcar registros existentes como tipo "number" (eran Float)
        try:
            result = conn.execute(text(
                "UPDATE monitoreo_detalles SET tipo_dato = 'number' WHERE tipo_dato IS NULL;"
            ))
            print(f"  ✅  Backfill completado: {result.rowcount} registros marcados como tipo_dato='number'.")
        except Exception as e:
            print(f"  ⚠️  Error en backfill: {e}")

        conn.commit()

    print("🏁 Migración Fase 88 completada exitosamente.")

if __name__ == "__main__":
    migrate()
