from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routers import convocatorias, solicitudes, estadisticas, auth, privado

app = FastAPI(
    title="API Subvenciones Bienestar Animal",
    description="Datos de convocatorias EPA y EELL de la DGDA (2021–2025)",
    version="0.1.0",
)

# En desarrollo permite llamadas desde cualquier origen (Live Server, file://, etc.).
# En producción con dominio propio, sustituir "*" por la URL del dominio.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(convocatorias.router)
app.include_router(solicitudes.router)
app.include_router(estadisticas.router)
app.include_router(auth.router)
app.include_router(privado.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    mensajes = {
        401: ("No autenticado", "Incluye un token JWT válido en la cabecera Authorization: Bearer <token>"),
        403: ("Acceso denegado", "Tu cuenta no tiene permisos suficientes para este recurso"),
        404: ("Recurso no encontrado", "Comprueba la URL o los parámetros de la petición"),
    }
    mensaje, sugerencia = mensajes.get(exc.status_code, (str(exc.detail), "Consulta la documentación en /docs"))
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.status_code, "mensaje": mensaje, "sugerencia": sugerencia},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": 422,
            "mensaje": "Datos de entrada inválidos",
            "sugerencia": "Revisa los campos requeridos y sus tipos",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": 500,
            "mensaje": "Error interno del servidor",
            "sugerencia": "Si el problema persiste, contacta con el administrador",
        },
    )


@app.get("/")
def root():
    return {"mensaje": "API funcionando"}
