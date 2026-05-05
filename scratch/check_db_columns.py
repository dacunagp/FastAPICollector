from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

# Common connection strings based on project files
urls = [
    "mysql+pymysql://root:1234@localhost:3306/gpconsul_monitoreos",
    "mysql+pymysql://admin:gp2026@localhost:3306/gpconsul_monitoreos",
    "mysql+pymysql://root:@localhost:3306/gpconsul_monitoreos"
]

def check_columns():
    for url in urls:
        try:
            engine = create_engine(url)
            inspector = inspect(engine)
            columns = inspector.get_columns('usuarios')
            print(f"SUCCESS with {url.split('@')[0]}")
            print("Columns in 'usuarios' table:")
            for column in columns:
                print(f"- {column['name']} ({column['type']})")
            return
        except Exception as e:
            print(f"FAILED with {url.split('@')[0]}: {str(e)[:100]}")

if __name__ == "__main__":
    check_columns()
