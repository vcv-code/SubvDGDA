from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional


# ──────────────────────────────────────────────
# CONVOCATORIAS
# ──────────────────────────────────────────────

class ConvocatoriaOut(BaseModel):
    id_convoc:          int
    titulo_convoc:      str
    tipo_convoc:        str
    anio_convocatoria:  int
    periodo_meses:      int
    fecha_convocatoria: Optional[date]
    fecha_resolucion:   Optional[date]

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# BENEFICIARIOS
# ──────────────────────────────────────────────

class BeneficiarioOut(BaseModel):
    id_benef:  int
    nombre:    str
    cif:       Optional[str]
    tipo_benef: str

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# SOLICITUDES
# ──────────────────────────────────────────────

class SolicitudOut(BaseModel):
    id_solic:       int
    num_expediente: Optional[str]
    puntuacion:     Optional[float]
    estado:         str
    convocatoria:   ConvocatoriaOut
    beneficiario:   BeneficiarioOut
    importe:        Optional[float]   # viene de concesiones, None si no fue concedida
    linea:          Optional[str]     # animales_abandonados | colonias_felinas | None

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# ESTADÍSTICAS
# Datos agregados para los gráficos del frontend
# ──────────────────────────────────────────────

class EstadisticaAnio(BaseModel):
    anio:          int
    tipo:          str          # "epa" o "eell"
    total:         int
    concedidas:    int
    no_beneficiarias: int
    excluidas:     int
    desistidas:    int
    importe_total: float

class EstadisticasOut(BaseModel):
    por_anio: list[EstadisticaAnio]
    total_registros:  int
    total_concedidas: int
    importe_global:   float


# ──────────────────────────────────────────────
# AUTENTICACIÓN
# ──────────────────────────────────────────────

class RegistroIn(BaseModel):
    email:    EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not any(c.islower() for c in v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v

class LoginIn(BaseModel):
    email:    EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type:   str

class UsuarioOut(BaseModel):
    id_usuario: int
    email:      str
    rol:        str
    activo:     bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
