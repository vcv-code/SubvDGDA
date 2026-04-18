from fastapi import APIRouter, Depends

from ..dependencies import require_rol
from ..models import Usuario

router = APIRouter(prefix="/privado", tags=["zona privada"])


@router.get("/perfil")
def perfil(usuario: Usuario = Depends(require_rol("registrado"))):
    """Devuelve los datos del usuario autenticado. Requiere rol: registrado o admin."""
    return {
        "email": usuario.email,
        "rol": usuario.rol,
        "miembro_desde": usuario.created_at,
    }


@router.get("/resumen-exclusivo")
def resumen_exclusivo(usuario: Usuario = Depends(require_rol("registrado"))):
    """
    Contenido exclusivo para usuarios registrados.
    Aquí irán consejos, fichas completas, comparativas, etc.
    """
    return {
        "mensaje": f"Bienvenida, {usuario.email}",
        "contenido": [
            "Historial completo de entidades por año",
            "Análisis de causas de exclusión más frecuentes",
            "Comparativa de importes por provincia y CCAA",
            "Puntuación mínima para ser concedida por convocatoria",
        ],
    }
