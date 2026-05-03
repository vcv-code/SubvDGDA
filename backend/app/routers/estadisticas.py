from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct
from ..db import get_db
from ..models import Solicitud, Convocatoria, Concesion, Beneficiario
from ..schemas import EstadisticasOut, EstadisticaAnio

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("/", response_model=EstadisticasOut)
def get_estadisticas(response: Response, db: Session = Depends(get_db)):
    """
    Devuelve totales agregados por año y tipo para los gráficos del frontend.
    Incluye conteos por estado e importe total concedido.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    filas = (
        db.query(
            Convocatoria.anio_convocatoria,
            Convocatoria.tipo_convoc,
            func.count(Solicitud.id_solic).label("total"),
            func.sum(case((Solicitud.estado == "concedida",       1), else_=0)).label("concedidas"),
            func.sum(case((Solicitud.estado == "no_beneficiaria", 1), else_=0)).label("no_beneficiarias"),
            func.sum(case((Solicitud.estado == "excluida",        1), else_=0)).label("excluidas"),
            func.sum(case((Solicitud.estado == "desistida",       1), else_=0)).label("desistidas"),
            func.coalesce(func.sum(Concesion.importe), 0).label("importe_total"),
        )
        .join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
        .outerjoin(Concesion, Concesion.id_solic == Solicitud.id_solic)
        .group_by(Convocatoria.anio_convocatoria, Convocatoria.tipo_convoc)
        .order_by(Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria)
        .all()
    )

    por_anio = [
        EstadisticaAnio(
            anio             = f.anio_convocatoria,
            tipo             = f.tipo_convoc,
            total            = f.total,
            concedidas       = f.concedidas,
            no_beneficiarias = f.no_beneficiarias,
            excluidas        = f.excluidas,
            desistidas       = f.desistidas,
            importe_total    = float(f.importe_total),
        )
        for f in filas
    ]

    entidades_unicas = db.query(func.count(distinct(Solicitud.id_benef))).scalar()

    return EstadisticasOut(
        por_anio         = por_anio,
        total_registros  = sum(f.total for f in filas),
        total_concedidas = sum(f.concedidas for f in filas),
        importe_global   = sum(float(f.importe_total) for f in filas),
        entidades_unicas = entidades_unicas,
    )
