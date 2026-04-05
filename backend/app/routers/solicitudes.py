from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..db import get_db
from ..models import Solicitud, Convocatoria
from ..schemas import SolicitudOut

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


@router.get("/", response_model=list[SolicitudOut])
def listar_solicitudes(
    anio:   Optional[int] = Query(None, description="Año de la convocatoria (2021–2025)"),
    tipo:   Optional[str] = Query(None, description="Tipo: epa o eell"),
    estado: Optional[str] = Query(None, description="Estado: concedida, no_beneficiaria, excluida, desistida"),
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
