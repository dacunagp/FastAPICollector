from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import catalogs, sync
from database import engine, Base
from logging_config import setup_logging

# --- Fase 86: Asegurar que las nuevas tablas (detalles) existan en la DB ---
Base.metadata.create_all(bind=engine)

# Inicializar Logs Narrativos y Errores
setup_logging()

app = FastAPI(title="API GP Consultores")

# Montar carpeta estática para poder ver las fotos desde el navegador (Ej: http://localhost:8000/static/uploads/foto.jpg)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registrar los routers
app.include_router(catalogs.router)
app.include_router(sync.router)

@app.get("/")
def read_root():
    return {"message": "API GP Consultores funcionando correctamente"}