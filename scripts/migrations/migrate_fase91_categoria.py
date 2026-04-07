"""
Fase 91 — Agregar columna 'categoria' a tabla 'parametros'
Ejecutar una SOLA VEZ para actualizar el esquema.
    python migrate_fase91_categoria.py
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🚀 Fase 91 — Iniciando adición de columna 'categoria' a tabla 'parametros'...")

    with engine.connect() as conn:
        try:
            print("  Wait... intentando agregar columna 'categoria'...")
            conn.execute(text(
                "ALTER TABLE parametros ADD COLUMN categoria VARCHAR(50) DEFAULT 'adicional';"
            ))
            print("  ✅  Columna 'categoria' agregada exitosamente.")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                print("  ℹ️  La columna 'categoria' ya existe en la tabla 'parametros'.")
            else:
                print(f"  ⚠️  Error al agregar la columna 'categoria': {e}")

        conn.commit()

    print("🏁 Migración Fase 91 completada exitosamente.")

if __name__ == "__main__":
    migrate()
