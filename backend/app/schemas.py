from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, computed_field
from datetime import date, datetime
from typing import Literal, Optional


# ──────────────────────────────────────────────
# CONVOCATORIAS
# ──────────────────────────────────────────────

class ConvocatoriaOut(BaseModel):
    id_convoc:          int
    num_convoc:         Optional[str]
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
    provincia:      Optional[str]     # solo EELL; None para EPA
    ccaa:           Optional[str]     # solo EELL; None para EPA
    es_agrupacion:  bool              # True si la concesión pertenece a una agrupación de municipios
    tramo:          Optional[int]     # 1, 2 o 3 (solo EELL 2025 concedidas); None en el resto
    causa_exclusion: Optional[str] = None  # código(s) separados por ";" (solo estado=excluida)

    model_config = ConfigDict(from_attributes=True)

class SolicitudesPageOut(BaseModel):
    total:      int
    resultados: list[SolicitudOut]


class CausaExclusionOut(BaseModel):
    """Entrada del catálogo de causas de exclusión: motivo legible de un código."""
    motivo:   str
    articulo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# AGRUPACIONES
# Desglose de municipios miembro (solo EELL 2025 concedidas como agrupación)
# ──────────────────────────────────────────────

class MiembroAgrupacionOut(BaseModel):
    nombre:           str
    cif:              Optional[str]
    importe_asignado: Optional[float]

    model_config = ConfigDict(from_attributes=True)

class AgrupacionOut(BaseModel):
    id_agrup:       int
    num_municipios: Optional[int]
    representante:  BeneficiarioOut
    miembros:       list[MiembroAgrupacionOut]

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

class UmbralLinea(BaseModel):
    linea:  str
    umbral: float

class UmbralAnio(BaseModel):
    tipo:       str                     # "epa" o "eell"
    anio:       int
    hubo_corte: bool                    # False = todas las admitidas obtuvieron subvención
    umbral:     Optional[float] = None  # puntuación mínima concedida (global); None si sin corte o si va por línea
    por_linea:  list[UmbralLinea] = []  # EPA de años con línea (2024+): umbral por cada línea

class EstadisticasOut(BaseModel):
    por_anio: list[EstadisticaAnio]
    total_registros:  int
    total_concedidas: int
    importe_global:   float
    entidades_unicas: int
    umbrales:         list[UmbralAnio] = []


# ──────────────────────────────────────────────
# ESTADÍSTICAS EPAs
# ──────────────────────────────────────────────

class TopBeneficiarioEpa(BaseModel):
    nombre:  str
    importe: float

class EpaAnio(BaseModel):
    anio:              int
    media:             float
    mediana:           float
    nuevos:            int
    recurrentes:       int
    # Solicitudes presentadas y concedidas ese año. Permiten calcular la tasa
    # de concesión, que cayó del 92 % en 2021 al 53 % en 2025: es el dato que
    # explica por qué hay protectoras que cumplen los requisitos y aun así se
    # quedan sin ayuda desde que en 2024 se introdujo el corte por puntuación.
    solicitudes:       int = 0
    concedidas:        int = 0
    top_beneficiarios: list[TopBeneficiarioEpa]

class RangoImporte(BaseModel):
    rango:    str
    cantidad: int

class ExclusionAnio(BaseModel):
    """Nº de solicitudes excluidas en un año (para la gráfica de evolución)."""
    anio:  int
    total: int

class CausaFrecuente(BaseModel):
    """Una causa de exclusión con su frecuencia (gráfica de causas más frecuentes)."""
    codigo: str
    motivo: str
    total:  int

class ExclusionesStats(BaseModel):
    """Bloque de exclusiones de las páginas de estadísticas.
    Las causas frecuentes son SOLO del último año con exclusiones, porque
    cada convocatoria usa su propia numeración de causas (no son mezclables)."""
    por_anio:          list[ExclusionAnio]   = []
    causas_anio:       Optional[int]         = None   # año al que pertenecen las causas
    causas_frecuentes: list[CausaFrecuente]  = []


class EstadisticasEpaOut(BaseModel):
    importe_medio:         float
    mediana:               float
    beneficiarios_unicos:  int
    nuevas_entidades:      int
    distribucion_importes: list[RangoImporte]
    por_anio:              list[EpaAnio]
    exclusiones:           ExclusionesStats = ExclusionesStats()


# ──────────────────────────────────────────────
# ESTADÍSTICAS EELL
# ──────────────────────────────────────────────

class CcaaItem(BaseModel):
    ccaa:             str
    importe_total:    float
    num_concesiones:  int

class ProvinciaItem(BaseModel):
    provincia:     str
    importe_total: float

class ConcentracionItem(BaseModel):
    top_10_pct: float
    resto_pct:  float

class EellAnioRecurrencia(BaseModel):
    anio:                int
    nuevas:              int
    recurrentes:         int
    recurrentes_nombres: list[str] = []

class EstadisticasEellOut(BaseModel):
    pct_ayuntamientos_con_ayuda: float
    importe_medio:               float
    ratio_exclusion:             float
    ccaa_top:                    str
    por_ccaa:                    list[CcaaItem]
    top_provincias:              list[ProvinciaItem]
    concentracion:               ConcentracionItem
    distribucion_importes:       list[RangoImporte]        = []
    exclusiones:                 ExclusionesStats          = ExclusionesStats()
    recurrencia_por_anio:        list[EellAnioRecurrencia] = []
    entidades_repiten:           int                       = 0
    total_entidades:             int                       = 0


# ──────────────────────────────────────────────
# AVISOS
# Convocatorias del año en curso sin resolución aún
# ──────────────────────────────────────────────

class AvisoOut(BaseModel):
    id_convoc:          int
    titulo_convoc:      str
    tipo_convoc:        str
    anio_convocatoria:  int
    fecha_convocatoria: Optional[date]
    fecha_fin_plazo:    Optional[date]
    fecha_resolucion:   Optional[date]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def estado_plazo(self) -> str:
        """Estado del plazo de solicitud calculado al vuelo:
        'sin_fecha' si no se conoce el fin de plazo, 'abierto' si aún no ha
        pasado y 'cerrado' si ya venció."""
        if self.fecha_fin_plazo is None:
            return "sin_fecha"
        return "abierto" if date.today() <= self.fecha_fin_plazo else "cerrado"


class FinPlazoIn(BaseModel):
    """Cuerpo para fijar (o borrar, con null) la fecha de fin de plazo de una convocatoria."""
    fecha_fin_plazo: Optional[date]


# ──────────────────────────────────────────────
# AUTENTICACIÓN
# ──────────────────────────────────────────────

def validar_password_segura(v: str) -> str:
    """Reglas de contraseña compartidas por todos los formularios que la piden.

    Estaba duplicada en cada schema; al centralizarla, cambiar una regla (o los
    mensajes que ve la usuaria) se hace en un solo sitio y no queda ningún
    formulario descolgado con las reglas antiguas.
    """
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in v):
        raise ValueError("La contraseña debe contener al menos una mayúscula")
    if not any(c.islower() for c in v):
        raise ValueError("La contraseña debe contener al menos una minúscula")
    if not any(c.isdigit() for c in v):
        raise ValueError("La contraseña debe contener al menos un número")
    return v


class ContactoIn(BaseModel):
    email:     EmailStr
    mensaje:   str
    nombre:    str = ""  # opcional
    sitio_web: str = ""  # honeypot: debe llegar vacío en envíos legítimos

    @field_validator("nombre")
    @classmethod
    def nombre_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 100:
            raise ValueError("El nombre no puede superar los 100 caracteres")
        return v

    @field_validator("mensaje")
    @classmethod
    def mensaje_valido(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("El mensaje debe tener al menos 10 caracteres")
        if len(v) > 2000:
            raise ValueError("El mensaje no puede superar los 2000 caracteres")
        return v


class ContactoOut(BaseModel):
    mensaje: str


class CambiarNombreIn(BaseModel):
    nombre: str

    @field_validator("nombre")
    @classmethod
    def nombre_valido(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        if len(v) > 100:
            raise ValueError("El nombre no puede superar los 100 caracteres")
        return v


class CambiarPasswordIn(BaseModel):
    contrasena_actual: str
    contrasena_nueva:  str

    @field_validator("contrasena_nueva")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        return validar_password_segura(v)

class LoginIn(BaseModel):
    email:    EmailStr
    password: str

class TokenOut(BaseModel):
    access_token:  str
    token_type:    str
    refresh_token: str

class RefreshIn(BaseModel):
    refresh_token: str

class UsuarioOut(BaseModel):
    id_usuario:       int
    email:            str
    nombre:           Optional[str] = None
    rol:              str
    activo:           bool
    email_verificado: bool
    created_at:       datetime

    model_config = ConfigDict(from_attributes=True)

class UsuariosPaginadosOut(BaseModel):
    usuarios: list[UsuarioOut]
    total:    int

class RecuperarPasswordIn(BaseModel):
    email: EmailStr

class ReenviarVerificacionIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token:            str
    contrasena_nueva: str

    @field_validator("contrasena_nueva")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        return validar_password_segura(v)


# ──────────────────────────────────────────────
# ADMIN
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# ZONA PRIVADA
# Resumen de solicitudes por tipo y año (contenido exclusivo)
# ──────────────────────────────────────────────

class ResumenFilaTabla(BaseModel):
    tipo:             str
    anio:             int
    total:            int
    concedidas:       int
    no_beneficiarias: int
    excluidas:        int
    desistidas:       int
    importe_total:    float

class ResumenTablaOut(BaseModel):
    filas:            list[ResumenFilaTabla]
    total_global:     int
    concedidas_total: int
    importe_global:   float


class CrearUsuarioIn(BaseModel):
    """Alta de usuario desde el panel admin.

    Sustituye al registro público: nadie se da de alta solo, las cuentas las
    crea la administradora. A diferencia del registro público, aquí NO hay
    honeypot (el endpoint ya está tras autenticación de admin) y sí se
    permite fijar el rol de entrada.
    """
    email:    EmailStr
    password: str
    nombre:   str = ""
    rol:      Literal["admin", "registrado"] = "registrado"

    @field_validator("password")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        return validar_password_segura(v)


class CambiarRolIn(BaseModel):
    rol: Literal["admin", "registrado"]

class CambiarActivoIn(BaseModel):
    activo: bool

class AdminEstadoOut(BaseModel):
    health:               str
    total_convocatorias:  int
    total_usuarios:       int
    total_solicitudes:    int
    ultima_convocatoria:  Optional[str]

class AdminLogsOut(BaseModel):
    lineas: list[str]
