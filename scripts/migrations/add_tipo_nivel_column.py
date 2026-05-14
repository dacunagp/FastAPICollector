"""
Migración: Agregar columna tipo_nivel a la tabla monitoreos.
Ejecutar una sola vez.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database import engine

def migrate():
    with engine.connect() as conn:
        conn.execute("ALTER TABLE monitoreos ADD COLUMN tipo_nivel VARCHAR(255) NULL AFTER tipo_pozo")
        conn.commit()
        print("✅ Columna 'tipo_nivel' agregada exitosamente a la tabla 'monitoreos'.")

if __name__ == "__main__":
    migrate()
