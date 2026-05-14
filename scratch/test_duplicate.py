
import logging
from database import SessionLocal
from models import MonitoreoDB
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_insert_duplicate():
    db = SessionLocal()
    try:
        # Intentar insertar un registro con un id_local que probablemente ya existe
        # Según el log, id_local=2 y device_id='MOBILE-DATA' existe.
        
        logger.info("Intentando insertar registro duplicado (id_local=2, device_id='MOBILE-DATA')...")
        
        nuevo = MonitoreoDB(
            device_id='MOBILE-DATA',
            id_local=2,
            fecha_hora_muestreo=datetime.now(),
            observacion="Test duplicado"
        )
        db.add(nuevo)
        db.commit()
        logger.info(f"✅ Éxito! Se creó un nuevo registro con ID: {nuevo.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error esperado o inesperado: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_insert_duplicate()
