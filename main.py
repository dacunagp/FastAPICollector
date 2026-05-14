from fastapi import FastAPI
from routers import catalogs, sync, analytics, email, comunicaciones, audit
from database import engine, Base
from logging_config import setup_logging

# --- Fase 86: Asegurar que las nuevas tablas (detalles) existan en la DB ---
Base.metadata.create_all(bind=engine)

# Inicializar Logs Narrativos y Errores
setup_logging()

app = FastAPI(title="API GP Consultores")

# Registrar los routers
app.include_router(catalogs.router)
app.include_router(sync.router)
app.include_router(analytics.router)
app.include_router(email.router)
app.include_router(comunicaciones.router)
app.include_router(audit.router)

@app.get("/")
def read_root():
    return {"message": "API GP Consultores funcionando correctamente"}