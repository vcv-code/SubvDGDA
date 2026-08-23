from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, DECIMAL, SmallInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .db import Base

# Modelos ORM que reflejan el esquema de la base de datos (modelo-fisico.sql).
# Relaciones: Convocatoria → Solicitud → Concesion → Agrupacion → AgrupacionMiembro
#             Beneficiario puede ser solicitante individual o representante de agrupación.


class Convocatoria(Base):
    __tablename__ = "convocatorias"

    id_convoc         = Column(Integer, primary_key=True, autoincrement=True)
    num_convoc        = Column(String(50), nullable=True)   # NULL en convocatorias históricas (pre-2026)
    titulo_convoc     = Column(String(255), nullable=False)
    tipo_convoc       = Column(Enum("epa", "eell"), nullable=False)
    anio_convocatoria = Column(Integer, nullable=False)
    fecha_convocatoria = Column(Date, nullable=True)
    fecha_fin_plazo   = Column(Date, nullable=True)         # fin del plazo de solicitud; NULL hasta que se conoce
    fecha_resolucion  = Column(Date, nullable=True)         # NULL mientras la resolución está pendiente
    periodo_meses     = Column(SmallInteger, nullable=False, default=12)  # 6 en EPA 2023/2024 y EELL 2023
    # Año de gasto que financia la convocatoria. NO es anio_convocatoria: las EPA
    # de 2021-2024 y todas las EELL pagan gastos del año siguiente.
    periodo_anio      = Column(String(16), nullable=True)
    periodo_matiz     = Column(String(40), nullable=True)   # p. ej. "1.er semestre"

    solicitudes = relationship("Solicitud", back_populates="convocatoria")


class Beneficiario(Base):
    __tablename__ = "beneficiarios"

    id_benef   = Column(Integer, primary_key=True, autoincrement=True)
    cif        = Column(String(20), nullable=True, unique=True)
    nombre     = Column(String(255), nullable=False)
    tipo_benef = Column(Enum("asociacion", "entidad_local"), nullable=False)

    solicitudes          = relationship("Solicitud", back_populates="beneficiario")
    agrupaciones_repr    = relationship("Agrupacion", back_populates="representante")   # municipio cabecera
    miembros_agrupacion  = relationship("AgrupacionMiembro", back_populates="beneficiario")


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id_solic       = Column(Integer, primary_key=True, autoincrement=True)
    id_convoc      = Column(Integer, ForeignKey("convocatorias.id_convoc"), nullable=False)
    id_benef       = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    num_expediente = Column(String(50), nullable=True)
    puntuacion     = Column(DECIMAL(5, 2), nullable=True)
    estado         = Column(Enum("concedida", "no_beneficiaria", "excluida", "desistida"), nullable=False)
    provincia      = Column(String(100), nullable=True)
    ccaa           = Column(String(100), nullable=True)
    causa_exclusion = Column(String(100), nullable=True)  # código(s) separados por ";" — leyenda en causas_exclusion

    convocatoria = relationship("Convocatoria", back_populates="solicitudes")
    beneficiario = relationship("Beneficiario", back_populates="solicitudes")
    concesion    = relationship("Concesion", back_populates="solicitud", uselist=False)  # 0 o 1 concesión


class CausaExclusion(Base):
    """Catálogo código -> motivo de las causas de exclusión, por (tipo, año).
    Cada convocatoria usa su propia numeración."""
    __tablename__ = "causas_exclusion"

    id_causa    = Column(Integer, primary_key=True, autoincrement=True)
    tipo_convoc = Column(Enum("epa", "eell"), nullable=False)
    anio        = Column(Integer, nullable=False)
    codigo      = Column(String(10), nullable=False)
    motivo      = Column(String(500), nullable=False)
    articulo    = Column(String(20), nullable=True)


class Concesion(Base):
    __tablename__ = "concesiones"

    id_conces = Column(Integer, primary_key=True, autoincrement=True)
    id_solic  = Column(Integer, ForeignKey("solicitudes.id_solic"), nullable=False, unique=True)
    importe   = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    linea     = Column(Enum("animales_abandonados", "colonias_felinas"), nullable=True)
    tramo     = Column(SmallInteger, nullable=True)  # tramo de población (solo EELL 2025)

    solicitud  = relationship("Solicitud", back_populates="concesion")
    agrupacion = relationship("Agrupacion", back_populates="concesion", uselist=False)


class Agrupacion(Base):
    """Agrupación de municipios EELL 2025: un municipio cabecera representa a varios miembros."""
    __tablename__ = "agrupaciones"

    id_agrup       = Column(Integer, primary_key=True, autoincrement=True)
    id_conces      = Column(Integer, ForeignKey("concesiones.id_conces"), nullable=False, unique=True)
    id_represent   = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    num_municipios = Column(Integer, nullable=True)

    concesion     = relationship("Concesion", back_populates="agrupacion")
    representante = relationship("Beneficiario", back_populates="agrupaciones_repr")
    miembros      = relationship("AgrupacionMiembro", back_populates="agrupacion")


class AgrupacionMiembro(Base):
    __tablename__ = "agrupacion_miembros"

    id_agrupM        = Column(Integer, primary_key=True, autoincrement=True)
    id_agrup         = Column(Integer, ForeignKey("agrupaciones.id_agrup"), nullable=False)
    id_benef         = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    importe_asignado = Column(DECIMAL(12, 2), nullable=True)  # importe individual dentro de la agrupación

    agrupacion   = relationship("Agrupacion", back_populates="miembros")
    beneficiario = relationship("Beneficiario", back_populates="miembros_agrupacion")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario       = Column(Integer, primary_key=True, autoincrement=True)
    email            = Column(String(255), nullable=False, unique=True)
    nombre           = Column(String(100), nullable=True)   # alias opcional; NULL si no lo ha definido
    password         = Column(String(255), nullable=False)
    rol              = Column(Enum("admin", "registrado"), nullable=False, default="registrado")
    activo           = Column(SmallInteger, nullable=False, default=1)
    email_verificado = Column(SmallInteger, nullable=False, default=0)  # registro siempre lo pone a 0
    created_at       = Column(DateTime, nullable=False)

    # Cada tipo de token tiene su propia tabla para poder invalidarlos de forma independiente
    refresh_tokens      = relationship("RefreshToken",      back_populates="usuario")
    reset_tokens        = relationship("ResetToken",        back_populates="usuario")
    verificacion_tokens = relationship("VerificacionToken", back_populates="usuario")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    token      = Column(String(64), nullable=False, unique=True)
    expira_en  = Column(DateTime, nullable=False)
    revocado   = Column(Boolean, nullable=False, default=False)  # rotación: al renovar, el anterior queda revocado

    usuario = relationship("Usuario", back_populates="refresh_tokens")


class ResetToken(Base):
    __tablename__ = "reset_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    token      = Column(String(64), nullable=False, unique=True)
    expira_en  = Column(DateTime, nullable=False)
    usado      = Column(Boolean, nullable=False, default=False)  # un solo uso; no se elimina para evitar reenvíos

    usuario = relationship("Usuario", back_populates="reset_tokens")


class VerificacionToken(Base):
    __tablename__ = "verificacion_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    token      = Column(String(64), nullable=False, unique=True)
    expira_en  = Column(DateTime, nullable=False)
    usado      = Column(Boolean, nullable=False, default=False)

    usuario = relationship("Usuario", back_populates="verificacion_tokens")
