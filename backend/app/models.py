from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, DECIMAL, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class Convocatoria(Base):
    __tablename__ = "convocatorias"

    id_convoc         = Column(Integer, primary_key=True, autoincrement=True)
    num_convoc        = Column(String(50), nullable=True)
    titulo_convoc     = Column(String(255), nullable=False)
    tipo_convoc       = Column(Enum("epa", "eell"), nullable=False)
    anio_convocatoria = Column(Integer, nullable=False)
    fecha_convocatoria = Column(Date, nullable=True)
    fecha_resolucion  = Column(Date, nullable=True)
    periodo_meses     = Column(SmallInteger, nullable=False, default=12)

    solicitudes = relationship("Solicitud", back_populates="convocatoria")


class Beneficiario(Base):
    __tablename__ = "beneficiarios"

    id_benef   = Column(Integer, primary_key=True, autoincrement=True)
    cif        = Column(String(20), nullable=True, unique=True)
    nombre     = Column(String(255), nullable=False)
    tipo_benef = Column(Enum("asociacion", "entidad_local"), nullable=False)

    solicitudes          = relationship("Solicitud", back_populates="beneficiario")
    agrupaciones_repr    = relationship("Agrupacion", back_populates="representante")
    miembros_agrupacion  = relationship("AgrupacionMiembro", back_populates="beneficiario")


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id_solic       = Column(Integer, primary_key=True, autoincrement=True)
    id_convoc      = Column(Integer, ForeignKey("convocatorias.id_convoc"), nullable=False)
    id_benef       = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    num_expediente = Column(String(50), nullable=True)
    puntuacion     = Column(DECIMAL(5, 2), nullable=True)
    estado         = Column(Enum("concedida", "no_beneficiaria", "excluida", "desistida"), nullable=False)

    convocatoria = relationship("Convocatoria", back_populates="solicitudes")
    beneficiario = relationship("Beneficiario", back_populates="solicitudes")
    concesion    = relationship("Concesion", back_populates="solicitud", uselist=False)


class Concesion(Base):
    __tablename__ = "concesiones"

    id_conces = Column(Integer, primary_key=True, autoincrement=True)
    id_solic  = Column(Integer, ForeignKey("solicitudes.id_solic"), nullable=False, unique=True)
    importe   = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    linea     = Column(Enum("animales_abandonados", "colonias_felinas"), nullable=True)
    tramo     = Column(SmallInteger, nullable=True)

    solicitud  = relationship("Solicitud", back_populates="concesion")
    agrupacion = relationship("Agrupacion", back_populates="concesion", uselist=False)


class Agrupacion(Base):
    __tablename__ = "agrupaciones"

    id_agrup       = Column(Integer, primary_key=True, autoincrement=True)
    id_conces      = Column(Integer, ForeignKey("concesiones.id_conces"), nullable=False, unique=True)
    id_represent   = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    num_municipios = Column(Integer, nullable=True)

    concesion    = relationship("Concesion", back_populates="agrupacion")
    representante = relationship("Beneficiario", back_populates="agrupaciones_repr")
    miembros     = relationship("AgrupacionMiembro", back_populates="agrupacion")


class AgrupacionMiembro(Base):
    __tablename__ = "agrupacion_miembros"

    id_agrupM        = Column(Integer, primary_key=True, autoincrement=True)
    id_agrup         = Column(Integer, ForeignKey("agrupaciones.id_agrup"), nullable=False)
    id_benef         = Column(Integer, ForeignKey("beneficiarios.id_benef"), nullable=False)
    importe_asignado = Column(DECIMAL(12, 2), nullable=True)

    agrupacion   = relationship("Agrupacion", back_populates="miembros")
    beneficiario = relationship("Beneficiario", back_populates="miembros_agrupacion")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    email      = Column(String(255), nullable=False, unique=True)
    password   = Column(String(255), nullable=False)
    rol        = Column(Enum("admin", "registrado"), nullable=False, default="registrado")
    activo     = Column(SmallInteger, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False)
