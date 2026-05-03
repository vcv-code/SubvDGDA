from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Convocatoria
from ..schemas import ConvocatoriaOut

router = APIRouter(prefix="/convocatorias", tags=["convocatorias"])


@router.get("/", response_model=list[ConvocatoriaOut])
def listar_convocatorias(response: Response, db: Session = Depends(get_db)):
    """Devuelve las 8 convocatorias del sistema (EPA 2021–2025 y EELL 2023–2025)."""
    response.headers["Cache-Control"] = "public, max-age=86400"
    return db.query(Convocatoria).order_by(Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria).all()
