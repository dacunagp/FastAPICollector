from database import engine
from sqlalchemy import text

if __name__ == "__main__":
    with engine.connect() as conn:
        result = conn.execute(text("DESCRIBE monitoreo_detalles;"))
        for row in result:
            print(row)
