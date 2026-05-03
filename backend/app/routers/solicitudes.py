import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..db import get_db
from ..models import Solicitud, Convocatoria, Beneficiario, Concesion
from ..schemas import SolicitudOut, SolicitudesPageOut

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "en", "con", "por", "para", "del", "al", "se", "es",
    "son", "que", "a", "e", "su", "sus", "le", "les", "lo", "no",
    "si", "pero", "más", "ya", "hay", "ser", "fue", "ha", "han",
}

def _palabras_clave(texto: str) -> list[str]:
    return [p for p in texto.lower().split() if p not in _STOPWORDS and len(p) > 2]


@router.get("/", response_model=SolicitudesPageOut)
def listar_solicitudes(
    anio:   Optional[int] = Query(None, description="Año de la convocatoria (2021–2025)"),
    tipo:   Optional[str] = Query(None, description="Tipo: epa o eell"),
    estado: Optional[str] = Query(None, description="Estado: concedida, no_beneficiaria, excluida, desistida"),
    linea:    Optional[str] = Query(None, description="Línea de actuación: animales_abandonados o colonias_felinas (solo EPA 2025)"),
    provincia: Optional[str] = Query(None, description="Provincia (solo EELL)"),
    ccaa:     Optional[str] = Query(None, description="Comunidad autónoma (solo EELL)"),
    cif:      Optional[str] = Query(None, description="CIF exacto del beneficiario"),
    buscar:   Optional[str] = Query(None, description="Búsqueda parcial por nombre de entidad (stopwords ignoradas)"),
    limite: int           = Query(100,  description="Máximo de resultados por página"),
    pagina: int           = Query(1,    description="Número de página (empieza en 1)"),
    db: Session = Depends(get_db),
):
    """
    Lista solicitudes con filtros opcionales.
    Devuelve `{"total": N, "resultados": [...]}` para que el frontend
    pueda mostrar el número total de páginas.
    """
    consulta = (
        db.query(Solicitud)
        .join(Convocatoria)
        .join(Beneficiario)
        .options(
            joinedload(Solicitud.convocatoria),
            joinedload(Solicitud.beneficiario),
            joinedload(Solicitud.concesion).joinedload(Concesion.agrupacion),
        )
    )

    if anio:
        consulta = consulta.filter(Convocatoria.anio_convocatoria == anio)
    if tipo:
        consulta = consulta.filter(Convocatoria.tipo_convoc == tipo)
    if estado:
        consulta = consulta.filter(Solicitud.estado == estado)
    if linea:
        consulta = consulta.filter(Solicitud.concesion.has(Concesion.linea == linea))
    if provincia:
        consulta = consulta.filter(Solicitud.provincia == provincia)
    if ccaa:
        consulta = consulta.filter(Solicitud.ccaa == ccaa)
    if cif:
        consulta = consulta.filter(Beneficiario.cif == cif)
    if buscar:
        for palabra in _palabras_clave(buscar):
            consulta = consulta.filter(Beneficiario.nombre.ilike(f"%{palabra}%"))

    total = consulta.count()
    offset = (pagina - 1) * limite
    solicitudes = consulta.offset(offset).limit(limite).all()

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
            linea          = s.concesion.linea if s.concesion else None,
            provincia      = s.provincia,
            ccaa           = s.ccaa,
            es_agrupacion  = bool(s.concesion and s.concesion.agrupacion),
        ))

    return SolicitudesPageOut(total=total, resultados=resultado)


@router.get("/export")
def exportar_csv(
    anio:      Optional[int] = Query(None),
    tipo:      Optional[str] = Query(None),
    estado:    Optional[str] = Query(None),
    linea:     Optional[str] = Query(None),
    provincia: Optional[str] = Query(None),
    ccaa:      Optional[str] = Query(None),
    cif:       Optional[str] = Query(None),
    buscar:    Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Descarga las solicitudes filtradas en formato CSV.
    Acepta los mismos filtros que GET /solicitudes/ pero devuelve todos los resultados sin paginar.
    """
    consulta = (
        db.query(Solicitud)
        .join(Convocatoria)
        .join(Beneficiario)
        .options(
            joinedload(Solicitud.convocatoria),
            joinedload(Solicitud.beneficiario),
            joinedload(Solicitud.concesion).joinedload(Concesion.agrupacion),
        )
    )

    if anio:
        consulta = consulta.filter(Convocatoria.anio_convocatoria == anio)
    if tipo:
        consulta = consulta.filter(Convocatoria.tipo_convoc == tipo)
    if estado:
        consulta = consulta.filter(Solicitud.estado == estado)
    if linea:
        consulta = consulta.filter(Solicitud.concesion.has(Concesion.linea == linea))
    if provincia:
        consulta = consulta.filter(Solicitud.provincia == provincia)
    if ccaa:
        consulta = consulta.filter(Solicitud.ccaa == ccaa)
    if cif:
        consulta = consulta.filter(Beneficiario.cif == cif)
    if buscar:
        for palabra in _palabras_clave(buscar):
            consulta = consulta.filter(Beneficiario.nombre.ilike(f"%{palabra}%"))

    solicitudes = consulta.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["anio", "tipo", "num_expediente", "entidad", "cif",
                     "estado", "importe", "linea", "provincia", "ccaa",
                     "puntuacion", "es_agrupacion"])
    for s in solicitudes:
        writer.writerow([
            s.convocatoria.anio_convocatoria,
            s.convocatoria.tipo_convoc,
            s.num_expediente,
            s.beneficiario.nombre,
            s.beneficiario.cif,
            s.estado,
            float(s.concesion.importe) if s.concesion else "",
            s.concesion.linea if s.concesion else "",
            s.provincia or "",
            s.ccaa or "",
            float(s.puntuacion) if s.puntuacion is not None else "",
            bool(s.concesion and s.concesion.agrupacion),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=solicitudes.csv"},
    )
