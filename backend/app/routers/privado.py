from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import hashear_password, verificar_password
from ..db import get_db
from ..dependencies import require_rol
from ..models import Usuario, RefreshToken
from ..schemas import CambiarPasswordIn

router = APIRouter(prefix="/privado", tags=["zona privada"])


@router.get("/perfil")
def perfil(usuario: Usuario = Depends(require_rol("registrado"))):
    """Devuelve los datos del usuario autenticado. Requiere rol: registrado o admin."""
    return {
        "id_usuario": usuario.id_usuario,
        "email": usuario.email,
        "rol": usuario.rol,
        "miembro_desde": usuario.created_at,
    }


@router.put("/cambiar-contrasena", status_code=status.HTTP_200_OK)
def cambiar_contrasena(
    datos: CambiarPasswordIn,
    usuario: Usuario = Depends(require_rol("registrado")),
    db: Session = Depends(get_db),
):
    """Cambia la contraseña del usuario autenticado. Requiere la contraseña actual."""
    if not verificar_password(datos.contrasena_actual, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta",
        )
    usuario.password = hashear_password(datos.contrasena_nueva)
    db.query(RefreshToken).filter(
        RefreshToken.id_usuario == usuario.id_usuario,
        RefreshToken.revocado == False,
    ).update({"revocado": True})
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


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
