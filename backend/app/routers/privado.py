from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import hashear_password, verificar_password
from ..db import get_db
from ..dependencies import require_rol
from ..models import Concesion, Solicitud, Convocatoria, Usuario, RefreshToken
from ..schemas import CambiarPasswordIn, ResumenTablaOut, ResumenFilaTabla

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
    return {
        "mensaje": f"Bienvenida, {usuario.email}",
        "contenido": [
            "Historial completo de entidades por año",
            "Análisis de causas de exclusión más frecuentes",
            "Comparativa de importes por provincia y CCAA",
            "Puntuación mínima para ser concedida por convocatoria",
        ],
    }


@router.get("/resumen-tabla", response_model=ResumenTablaOut)
def resumen_tabla(
    usuario: Usuario = Depends(require_rol("registrado")),
    db: Session = Depends(get_db),
):
    """Tabla resumen de solicitudes por tipo y año. Requiere rol: registrado o admin."""
    filas = []
    total_global     = 0
    concedidas_total = 0
    importe_global   = 0.0

    convocatorias = db.query(Convocatoria).order_by(
        Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria
    ).all()

    for conv in convocatorias:
        solicitudes = db.query(Solicitud).filter(Solicitud.id_convoc == conv.id_convoc).all()
        total    = len(solicitudes)
        conced   = sum(1 for s in solicitudes if s.estado == "concedida")
        no_benef = sum(1 for s in solicitudes if s.estado == "no_beneficiaria")
        excl     = sum(1 for s in solicitudes if s.estado == "excluida")
        desist   = sum(1 for s in solicitudes if s.estado == "desistida")

        ids_conced = [s.id_solic for s in solicitudes if s.estado == "concedida"]
        importe = 0.0
        if ids_conced:
            concesiones = db.query(Concesion).filter(Concesion.id_solic.in_(ids_conced)).all()
            importe = float(sum(c.importe for c in concesiones if c.importe))

        filas.append(ResumenFilaTabla(
            tipo=conv.tipo_convoc,
            anio=conv.anio_convocatoria,
            total=total,
            concedidas=conced,
            no_beneficiarias=no_benef,
            excluidas=excl,
            desistidas=desist,
            importe_total=round(importe, 2),
        ))

        total_global     += total
        concedidas_total += conced
        importe_global   += importe

    return ResumenTablaOut(
        filas=filas,
        total_global=total_global,
        concedidas_total=concedidas_total,
        importe_global=round(importe_global, 2),
    )
