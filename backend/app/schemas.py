from pydantic import BaseModel, ConfigDict
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

class LoginIn(BaseModel):
    email:    str
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
