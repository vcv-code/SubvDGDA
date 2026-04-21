from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..db import get_db
from ..models import Solicitud, Convocatoria, Beneficiario
from ..schemas import SolicitudOut

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "en", "con", "por", "para", "del", "al", "se", "es",
    "son", "que", "a", "e", "su", "sus", "le", "les", "lo", "no",
    "si", "pero", "más", "ya", "hay", "ser", "fue", "ha", "han",
}

def _palabras_clave(texto: str) -> list[str]:
    return [p for p in texto.lower().split() if p not in _STOPWORDS and len(p) > 2]


@router.get("/", response_model=list[SolicitudOut])
def listar_solicitudes(
    anio:   Optional[int] = Query(None, description="Año de la convocatoria (2021–2025)"),
    tipo:   Optional[str] = Query(None, description="Tipo: epa o eell"),
    estado: Optional[str] = Query(None, description="Estado: concedida, no_beneficiaria, excluida, desistida"),
    buscar: Optional[str] = Query(None, description="Búsqueda parcial por nombre de entidad (stopwords ignoradas)"),
    limite: int           = Query(100,  description="Máximo de resultados por página"),
    pagina: int           = Query(1,    description="Número de página (empieza en 1)"),
    db: Session = Depends(get_db),
):
    """
    Lista solicitudes con filtros opcionales por año, tipo y estado.
    Paginación con los parámetros `limite` y `pagina`.
    """
    consulta = (
        db.query(Solicitud)
        .join(Convocatoria)
        .join(Beneficiario)
        .options(
            joinedload(Solicitud.convocatoria),
            joinedload(Solicitud.beneficiario),
            joinedload(Solicitud.concesion),
        )
    )

    if anio:
        consulta = consulta.filter(Convocatoria.anio_convocatoria == anio)
    if tipo:
        consulta = consulta.filter(Convocatoria.tipo_convoc == tipo)
    if estado:
        consulta = consulta.filter(Solicitud.estado == estado)
    if buscar:
        for palabra in _palabras_clave(buscar):
            consulta = consulta.filter(Beneficiario.nombre.ilike(f"%{palabra}%"))

    offset = (pagina - 1) * limite
    solicitudes = consulta.offset(offset).limit(limite).all()

    # Construimos la respuesta manualmente porque `importe` no está en solicitudes
    # sino en la tabla concesiones (accesible via solicitud.concesion)
    resultado = []
    for s in solicitudes:
        resultado.append(SolicitudOut(
            id_solic       = s.id_solic,
            num_expediente = s.num_expediente,
            puntuacion     = float(s.puntuacion) if s.puntuacion is not None else None,
            estado         = s.estado,
            convocatoria   = s.convocatoria,
            beneficiario   = s.beneficiario,
            importe        = float(s.concesion.importe) if s.concesion else None,
        ))

    return resultado
