import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import require_rol
from ..models import Convocatoria, RefreshToken, ResetToken, VerificacionToken, Solicitud, Usuario
from ..schemas import (
    AdminEstadoOut,
    AdminLogsOut,
    AvisoOut,
    CambiarActivoIn,
    CambiarRolIn,
    UsuarioOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

LOG_FILE = os.getenv("LOG_DIR", "/app/logs") + "/access.log"


# ── Estado general ────────────────────────────────────────────────────────────

@router.get("/estado", response_model=AdminEstadoOut)
def estado(
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    total_conv   = db.query(func.count(Convocatoria.id_convoc)).scalar()
    total_usrs   = db.query(func.count(Usuario.id_usuario)).scalar()
    total_solic  = db.query(func.count(Solicitud.id_solic)).scalar()

    ultima = (
        db.query(Convocatoria)
        .order_by(Convocatoria.anio_convocatoria.desc(),
                  Convocatoria.fecha_convocatoria.desc())
        .first()
    )
    ultima_str = (
        f"{ultima.titulo_convoc} ({ultima.anio_convocatoria})" if ultima else None
    )

    return AdminEstadoOut(
        health="ok",
        total_convocatorias=total_conv,
        total_usuarios=total_usrs,
        total_solicitudes=total_solic,
        ultima_convocatoria=ultima_str,
    )


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios(
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    return db.query(Usuario).order_by(Usuario.created_at.desc()).all()


@router.patch("/usuarios/{id_usuario}/rol", response_model=UsuarioOut)
def cambiar_rol(
    id_usuario: int,
    datos: CambiarRolIn,
    admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    if id_usuario == admin.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol",
        )
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    usuario.rol = datos.rol
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/usuarios/{id_usuario}/activo", response_model=UsuarioOut)
def cambiar_activo(
    id_usuario: int,
    datos: CambiarActivoIn,
    admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    if id_usuario == admin.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    usuario.activo = 1 if datos.activo else 0
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/usuarios/{id_usuario}", status_code=status.HTTP_200_OK)
def eliminar_usuario(
    id_usuario: int,
    admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    if id_usuario == admin.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta",
        )
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    db.query(RefreshToken).filter(RefreshToken.id_usuario == id_usuario).delete()
    db.query(ResetToken).filter(ResetToken.id_usuario == id_usuario).delete()
    db.query(VerificacionToken).filter(VerificacionToken.id_usuario == id_usuario).delete()
    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado"}


# ── Avisos (convocatorias sin resolución) ─────────────────────────────────────

@router.get("/avisos", response_model=list[AvisoOut])
def listar_avisos(
    incluir_resueltas: bool = Query(False),
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    q = db.query(Convocatoria)
    if not incluir_resueltas:
        q = q.filter(Convocatoria.fecha_resolucion.is_(None))
    return q.order_by(Convocatoria.anio_convocatoria.desc()).all()


@router.patch("/avisos/{id_convoc}/desactivar", response_model=AvisoOut)
def desactivar_aviso(
    id_convoc: int,
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    convoc = db.query(Convocatoria).filter(Convocatoria.id_convoc == id_convoc).first()
    if not convoc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")
    if convoc.fecha_resolucion is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La convocatoria ya tiene fecha de resolución",
        )
    convoc.fecha_resolucion = date.today()
    db.commit()
    db.refresh(convoc)
    return convoc


@router.patch("/avisos/{id_convoc}/reactivar", response_model=AvisoOut)
def reactivar_aviso(
    id_convoc: int,
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    convoc = db.query(Convocatoria).filter(Convocatoria.id_convoc == id_convoc).first()
    if not convoc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")
    if convoc.fecha_resolucion is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La convocatoria ya está activa",
        )
    convoc.fecha_resolucion = None
    db.commit()
    db.refresh(convoc)
    return convoc


@router.delete("/avisos/{id_convoc}", status_code=status.HTTP_200_OK)
def eliminar_aviso(
    id_convoc: int,
    _admin: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    convoc = db.query(Convocatoria).filter(Convocatoria.id_convoc == id_convoc).first()
    if not convoc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")
    tiene_solicitudes = db.query(Solicitud).filter(Solicitud.id_convoc == id_convoc).first()
    if tiene_solicitudes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: la convocatoria tiene solicitudes asociadas",
        )
    db.delete(convoc)
    db.commit()
    return {"mensaje": "Convocatoria eliminada"}


# ── Logs ──────────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=AdminLogsOut)
def ver_logs(
    n: int = Query(100, ge=1, le=500),
    _admin: Usuario = Depends(require_rol("admin")),
):
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lineas = f.readlines()
        return AdminLogsOut(lineas=[l.rstrip() for l in lineas[-n:]])
    except FileNotFoundError:
        return AdminLogsOut(lineas=["(archivo de log no disponible)"])
