from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Convocatoria
from ..schemas import AvisoOut

router = APIRouter(prefix="/avisos", tags=["avisos"])


@router.get("/", response_model=list[AvisoOut])
def get_avisos(db: Session = Depends(get_db)):
    """
    Devuelve las convocatorias del año en curso que aún no tienen resolución
    (fecha_resolucion IS NULL). El frontend las usa para mostrar el banner
    "convocatoria en tramitación, datos disponibles cuando se publique la resolución".
    """
    anio_actual = date.today().year
    return (
        db.query(Convocatoria)
        .filter(
            Convocatoria.fecha_resolucion.is_(None),
            Convocatoria.anio_convocatoria == anio_actual,
        )
        .order_by(Convocatoria.fecha_convocatoria)
        .all()
    )
