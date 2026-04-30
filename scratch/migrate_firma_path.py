from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Adding firma_path column to monitoreos table...")
    try:
        conn.execute(text("ALTER TABLE monitoreos ADD COLUMN firma_path VARCHAR(255) DEFAULT NULL AFTER foto_muestreo;"))
        conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error or already exists: {e}")
