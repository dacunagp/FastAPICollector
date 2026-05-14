
import sqlalchemy
from sqlalchemy import create_engine, inspect

db_url = "mysql+pymysql://admin:gp2026@localhost:3306/gpconsul_monitoreos"
engine = create_engine(db_url)
inspector = inspect(engine)

print(f"Columns in 'usuarios':")
for column in inspector.get_columns('usuarios'):
    print(f" - {column['name']} ({column['type']})")
