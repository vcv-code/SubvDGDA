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
    Devuelve las convocatorias sin resolución (fecha_resolucion IS NULL) del año
    en curso y del anterior. El frontend las usa para el banner "convocatoria en
    tramitación, datos disponibles cuando podamos obtenerlos tras la resolución".

    Por qué el año anterior y no solo el actual
    -------------------------------------------
    Filtrando por `anio_convocatoria == anio_actual`, el aviso desaparecía el 1
    de enero a las 00:00 aunque la convocatoria siguiera sin resolver: se iba
    porque cambiaba el año, no porque hubiera pasado nada. Y las resoluciones
    tardías son normales aquí —las EPA de un año se han resuelto ya en el
    siguiente—, así que la web habría dejado de anunciar "en tramitación"
    justo mientras seguía siendo cierto.

    Incluyendo el año anterior, el aviso se retira cuando llega la resolución,
    que es lo que significa. El corte en dos años evita que una convocatoria
    antigua sin resolver se quede anunciándose para siempre.
    """
    anio_actual = date.today().year
    return (
        db.query(Convocatoria)
        .filter(
            Convocatoria.fecha_resolucion.is_(None),
            Convocatoria.anio_convocatoria >= anio_actual - 1,
        )
        .order_by(Convocatoria.fecha_convocatoria)
        .all()
    )
