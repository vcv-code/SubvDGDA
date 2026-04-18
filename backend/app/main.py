from fastapi import FastAPI
from .routers import convocatorias, solicitudes, estadisticas, auth, privado

app = FastAPI(
    title="API Subvenciones Bienestar Animal",
    description="Datos de convocatorias EPA y EELL de la DGDA (2021–2025)",
    version="0.1.0",
)

app.include_router(convocatorias.router)
app.include_router(solicitudes.router)
app.include_router(estadisticas.router)
app.include_router(auth.router)
app.include_router(privado.router)


@app.get("/")
def root():
    return {"mensaje": "API funcionando"}
