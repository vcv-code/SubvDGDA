from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import (hashear_password, verificar_password, crear_token,
                    crear_refresh_token, refresh_expira_en,
                    crear_reset_token, reset_expira_en, enviar_email_recuperacion)
from ..db import get_db
from ..models import Usuario, RefreshToken, ResetToken
from ..schemas import RegistroIn, LoginIn, TokenOut, UsuarioOut, RefreshIn, RecuperarPasswordIn, ResetPasswordIn

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroIn, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta con ese email",
        )
    usuario = Usuario(
        email=datos.email,
        password=hashear_password(datos.password),
        rol="registrado",
        activo=1,
        created_at=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verificar_password(datos.password, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )
    access_token  = crear_token(usuario.email, usuario.rol)
    refresh_token = crear_refresh_token()
    db.add(RefreshToken(
        id_usuario=usuario.id_usuario,
        token=refresh_token,
        expira_en=refresh_expira_en(),
    ))
    db.commit()
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=TokenOut)
def refresh(datos: RefreshIn, db: Session = Depends(get_db)):
    rt = db.query(RefreshToken).filter(RefreshToken.token == datos.refresh_token).first()
    if not rt or rt.revocado or rt.expira_en.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == rt.id_usuario).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    nuevo_access = crear_token(usuario.email, usuario.rol)
    nuevo_refresh = crear_refresh_token()
    rt.revocado = True
    db.add(RefreshToken(id_usuario=usuario.id_usuario, token=nuevo_refresh, expira_en=refresh_expira_en()))
    db.commit()
    return {"access_token": nuevo_access, "token_type": "bearer", "refresh_token": nuevo_refresh}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(datos: RefreshIn, db: Session = Depends(get_db)):
    rt = db.query(RefreshToken).filter(RefreshToken.token == datos.refresh_token).first()
    if rt and not rt.revocado:
        rt.revocado = True
        db.commit()
    return {"mensaje": "Sesión cerrada"}


@router.post("/recuperar", status_code=status.HTTP_200_OK)
def recuperar_password(datos: RecuperarPasswordIn, db: Session = Depends(get_db)):
    # Respondemos siempre igual para no revelar si el email existe o no
    respuesta = {"mensaje": "Si ese email está registrado, recibirás un enlace en breve"}
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not usuario.activo:
        return respuesta
    token = crear_reset_token()
    db.add(ResetToken(
        id_usuario=usuario.id_usuario,
        token=token,
        expira_en=reset_expira_en(),
    ))
    db.commit()
    enviar_email_recuperacion(usuario.email, token)
    return respuesta


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_password(datos: ResetPasswordIn, db: Session = Depends(get_db)):
    rt = db.query(ResetToken).filter(ResetToken.token == datos.token).first()
    if not rt or rt.usado or rt.expira_en.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace inválido o expirado")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == rt.id_usuario).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace inválido o expirado")
    usuario.password = hashear_password(datos.contrasena_nueva)
    rt.usado = True
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}
