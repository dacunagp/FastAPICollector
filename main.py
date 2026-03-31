from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import catalogs, sync

app = FastAPI(title="API GP Consultores")

# Montar carpeta estática para poder ver las fotos desde el navegador (Ej: http://localhost:8000/static/uploads/foto.jpg)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registrar los routers
app.include_router(catalogs.router)
app.include_router(sync.router)

@app.get("/")
def read_root():
    return {"message": "API GP Consultores funcionando correctamente"}