from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..db import get_db
from ..models import Solicitud, Concesion, Agrupacion, AgrupacionMiembro
from ..schemas import AgrupacionOut, MiembroAgrupacionOut, BeneficiarioOut

router = APIRouter(prefix="/agrupaciones", tags=["agrupaciones"])


@router.get("/{id_solic}", response_model=AgrupacionOut)
def detalle_agrupacion(id_solic: int, db: Session = Depends(get_db)):
    """
    Devuelve el desglose de municipios miembro de una agrupación EELL.
    Solo existe para solicitudes con es_agrupacion=true.
    """
    solicitud = (
        db.query(Solicitud)
        .options(
            joinedload(Solicitud.concesion)
            .joinedload(Concesion.agrupacion)
            .joinedload(Agrupacion.miembros)
            .joinedload(AgrupacionMiembro.beneficiario),
            joinedload(Solicitud.concesion)
            .joinedload(Concesion.agrupacion)
            .joinedload(Agrupacion.representante),
        )
        .filter(Solicitud.id_solic == id_solic)
        .first()
    )

    if not solicitud or not solicitud.concesion or not solicitud.concesion.agrupacion:
        raise HTTPException(status_code=404, detail="Agrupación no encontrada")

    agrup = solicitud.concesion.agrupacion
    return AgrupacionOut(
        id_agrup=agrup.id_agrup,
        num_municipios=agrup.num_municipios,
        representante=BeneficiarioOut.model_validate(agrup.representante),
        miembros=[
            MiembroAgrupacionOut(
                nombre=m.beneficiario.nombre,
                cif=m.beneficiario.cif,
                importe_asignado=float(m.importe_asignado) if m.importe_asignado is not None else None,
            )
            for m in agrup.miembros
        ],
    )
