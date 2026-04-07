"""
Fase 97 — Limpieza Manual: Eliminar datos de prueba 'caudal' con valor '0.02'
Ejecutar para limpiar la base de datos de registros de prueba que afectan estadísticas.
    python scripts/utils/cleanup_caudal_test.py
"""
import sys
import os

# Añadir el directorio raíz al path para poder importar database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database import engine
from sqlalchemy import text

def cleanup():
    print("🚀 Fase 97 — Iniciando limpieza de datos de prueba 'caudal'...")

    with engine.connect() as conn:
        try:
            # 1. Contar registros antes de borrar (opcional, para feedback)
            res = conn.execute(text(
                "SELECT COUNT(*) FROM monitoreo_detalles WHERE parametro = 'caudal' AND valor = '0.02';"
            )).fetchone()
            count = res[0] if res else 0
            
            if count > 0:
                print(f"  🔍 Encontrados {count} registros de prueba. Procediendo a eliminar...")
                conn.execute(text(
                    "DELETE FROM monitoreo_detalles WHERE parametro = 'caudal' AND valor = '0.02';"
                ))
                print(f"  ✅  Limpieza completada exitosamente.")
            else:
                print("  ℹ️  No se encontraron registros de prueba 'caudal' con valor '0.02'.")
            
            conn.commit()
        except Exception as e:
            print(f"  ⚠️  Error durante la limpieza: {e}")

    print("🏁 Proceso de limpieza finalizado.")

if __name__ == "__main__":
    cleanup()
