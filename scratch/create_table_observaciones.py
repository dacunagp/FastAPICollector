import os
import sys

# Añadir el directorio padre al sys.path si es necesario, o simplemente ejecutar desde FastAPICollector
sys.path.append("/home/ubuntu/FastAPICollector")

from sqlalchemy import text
from database import engine

def create_and_seed():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS observaciones_predefinidas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            texto VARCHAR(255) NOT NULL,
            categoria VARCHAR(50) DEFAULT NULL,
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """))
        
        # Check if table is empty before seeding
        result = conn.execute(text("SELECT COUNT(*) FROM observaciones_predefinidas")).scalar()
        if result == 0:
            conn.execute(text("""
            INSERT INTO observaciones_predefinidas (texto, categoria) VALUES
            ('Pozo seco', NULL),
            ('Bomba en mantención', NULL),
            ('Sin acceso al punto', NULL),
            ('Muestra con sedimentos', NULL);
            """))
            print("Seed data inserted.")
        else:
            print("Table already has data.")
        
        conn.commit()

if __name__ == "__main__":
    create_and_seed()
