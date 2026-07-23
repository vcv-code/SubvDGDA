import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from ..db import get_db
from ..models import Solicitud, Convocatoria, Beneficiario, Concesion, CausaExclusion
from ..schemas import SolicitudOut, SolicitudesPageOut, CausaExclusionOut

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "en", "con", "por", "para", "del", "al", "se", "es",
    "son", "que", "a", "e", "su", "sus", "le", "les", "lo", "no",
    "si", "pero", "más", "ya", "hay", "ser", "fue", "ha", "han",
}

def _palabras_clave(texto: str) -> list[str]:
    # Se conservan tokens > 2 chars y dígitos (p.ej. "4" en "4 GATOS Y TU").
    # Las stopwords siguen filtrándose; los tokens cortos no numéricos (tu, ti, lo)
    # se descartan para evitar coincidencias triviales.
    return [
        p for p in texto.lower().split()
        if p not in _STOPWORDS and (len(p) > 2 or p.isdigit())
    ]


@router.get("/", response_model=SolicitudesPageOut)
def listar_solicitudes(
    anio:   Optional[int] = Query(None, description="Año de la convocatoria (2021–2025)"),
    tipo:   Optional[str] = Query(None, description="Tipo: epa o eell"),
    estado: Optional[str] = Query(None, description="Estado: concedida, no_beneficiaria, excluida, desistida"),
    linea:    Optional[str] = Query(None, description="Línea de actuación: animales_abandonados o colonias_felinas (EPA 2024 y 2025)"),
    provincia: Optional[str] = Query(None, description="Provincia (solo EELL)"),
    ccaa:     Optional[str] = Query(None, description="Comunidad autónoma (solo EELL)"),
    causa:    Optional[str] = Query(None, max_length=10, description="Código de causa de exclusión (leyenda por tipo+año en GET /solicitudes/causas)"),
    cif:      Optional[str] = Query(None, description="CIF exacto del beneficiario"),
    buscar:   Optional[str] = Query(None, max_length=200, description="Búsqueda parcial por nombre de entidad (stopwords ignoradas)"),
    orden:  Optional[str] = Query("entidad-az", description="Orden: entidad-az, importe-desc, importe-asc"),
    limite: int           = Query(100, ge=1, le=500, description="Máximo de resultados por página"),
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
    if causa:
        # causa_exclusion guarda código(s) separados por ";" ("2;6.a").
        # Match por token exacto para que "6" no case con "16" ni con "6.a".
        # LIKE portable (MariaDB y SQLite de los tests), sin funciones propietarias.
        consulta = consulta.filter(or_(
            Solicitud.causa_exclusion == causa,
            Solicitud.causa_exclusion.like(f"{causa};%"),
            Solicitud.causa_exclusion.like(f"%;{causa}"),
            Solicitud.causa_exclusion.like(f"%;{causa};%"),
        ))
    if cif:
        consulta = consulta.filter(Beneficiario.cif == cif)
    if buscar:
        # Cada token debe aparecer en el nombre O (si tiene >=4 chars) en el
        # num_expediente. El umbral evita que tokens cortos como "4" o "20"
        # exploten los resultados al hacer match con casi cualquier expediente
        # ("2024B...", "EXP/100040"...). Tokens largos como "100024", "B651"
        # o "EXP/100024" sí buscan tambien en num_expediente.
        for palabra in _palabras_clave(buscar):
            patron = f"%{palabra}%"
            if len(palabra) >= 4:
                consulta = consulta.filter(
                    or_(
                        Beneficiario.nombre.ilike(patron),
                        Solicitud.num_expediente.ilike(patron),
                    )
                )
            else:
                consulta = consulta.filter(Beneficiario.nombre.ilike(patron))

    total = consulta.count()
    offset = (pagina - 1) * limite

    if orden in ("importe-desc", "importe-asc"):
        importe_subq = (
            db.query(Concesion.importe)
            .filter(Concesion.id_solic == Solicitud.id_solic)
            .correlate(Solicitud)
            .scalar_subquery()
        )
        consulta = consulta.order_by(
            importe_subq.desc() if orden == "importe-desc" else importe_subq.asc()
        )
    else:
        consulta = consulta.order_by(Beneficiario.nombre.asc())

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
            tramo          = s.concesion.tramo if s.concesion else None,
            causa_exclusion = s.causa_exclusion,
        ))

    return SolicitudesPageOut(total=total, resultados=resultado)


@router.get("/causas", response_model=dict[str, dict[str, dict[str, CausaExclusionOut]]])
def catalogo_causas(response: Response, db: Session = Depends(get_db)):
    """
    Catálogo código → motivo de las causas de exclusión, agrupado por tipo y año:
    `{"epa": {"2024": {"3.1": {"motivo": ..., "articulo": ...}, ...}}, "eell": {...}}`.
    Cada convocatoria usa su propia numeración, por eso la leyenda va por (tipo, año).
    Cache-Control: 24 h — es un catálogo histórico que no cambia.
    """
    response.headers["Cache-Control"] = "public, max-age=86400"

    filas = (
        db.query(CausaExclusion)
        .order_by(CausaExclusion.tipo_convoc, CausaExclusion.anio, CausaExclusion.id_causa)
        .all()
    )
    catalogo: dict = {}
    for f in filas:
        catalogo.setdefault(f.tipo_convoc, {}).setdefault(str(f.anio), {})[f.codigo] = \
            CausaExclusionOut(motivo=f.motivo, articulo=f.articulo)
    return catalogo


@router.get("/export")
def exportar_csv(
    anio:      Optional[int] = Query(None),
    tipo:      Optional[str] = Query(None),
    estado:    Optional[str] = Query(None),
    linea:     Optional[str] = Query(None),
    provincia: Optional[str] = Query(None),
    ccaa:      Optional[str] = Query(None),
    causa:     Optional[str] = Query(None, max_length=10),
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
    if causa:
        # causa_exclusion guarda código(s) separados por ";" ("2;6.a").
        # Match por token exacto para que "6" no case con "16" ni con "6.a".
        # LIKE portable (MariaDB y SQLite de los tests), sin funciones propietarias.
        consulta = consulta.filter(or_(
            Solicitud.causa_exclusion == causa,
            Solicitud.causa_exclusion.like(f"{causa};%"),
            Solicitud.causa_exclusion.like(f"%;{causa}"),
            Solicitud.causa_exclusion.like(f"%;{causa};%"),
        ))
    if cif:
        consulta = consulta.filter(Beneficiario.cif == cif)
    if buscar:
        # Cada token debe aparecer en el nombre O (si tiene >=4 chars) en el
        # num_expediente. El umbral evita que tokens cortos como "4" o "20"
        # exploten los resultados al hacer match con casi cualquier expediente
        # ("2024B...", "EXP/100040"...). Tokens largos como "100024", "B651"
        # o "EXP/100024" sí buscan tambien en num_expediente.
        for palabra in _palabras_clave(buscar):
            patron = f"%{palabra}%"
            if len(palabra) >= 4:
                consulta = consulta.filter(
                    or_(
                        Beneficiario.nombre.ilike(patron),
                        Solicitud.num_expediente.ilike(patron),
                    )
                )
            else:
                consulta = consulta.filter(Beneficiario.nombre.ilike(patron))

    total_export = consulta.count()
    if total_export > 5000:
        raise HTTPException(
            status_code=400,
            detail="Demasiados resultados para exportar. Aplica filtros para reducirlos.",
        )

    solicitudes = consulta.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["anio", "tipo", "num_expediente", "entidad", "cif",
                     "estado", "importe", "linea", "tramo", "provincia", "ccaa",
                     "puntuacion", "es_agrupacion", "causa_exclusion"])
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
            s.concesion.tramo if s.concesion else "",
            s.provincia or "",
            s.ccaa or "",
            float(s.puntuacion) if s.puntuacion is not None else "",
            bool(s.concesion and s.concesion.agrupacion),
            s.causa_exclusion or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=solicitudes.csv"},
    )
