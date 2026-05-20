import logging
import os
import time

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logger import setup_logging
from .routers import convocatorias, solicitudes, estadisticas, auth, privado, agrupaciones, avisos, admin

logger = setup_logging()

app = FastAPI(
    title="API Subvenciones Bienestar Animal",
    description="Datos de convocatorias EPA y EELL de la DGDA (2021–2025)",
    version="0.1.0",
)

# Orígenes permitidos desde variable de entorno (separados por coma).
# Desarrollo: CORS_ORIGINS=* en .env. Producción: CORS_ORIGINS=https://mi-dominio.com
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(
        "%s | %s %s | %s | %sms",
        request.client.host if request.client else "-",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response

app.include_router(convocatorias.router)
app.include_router(solicitudes.router)
app.include_router(estadisticas.router)
app.include_router(auth.router)
app.include_router(privado.router)
app.include_router(agrupaciones.router)
app.include_router(avisos.router)
app.include_router(admin.router)


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
    logger.error("%s %s | %s: %s", request.method, request.url.path, type(exc).__name__, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": 500,
            "mensaje": "Error interno del servidor",
            "sugerencia": "Si el problema persiste, contacta con el administrador",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"mensaje": "API funcionando"}
