from collections import defaultdict
from statistics import median

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct

from ..db import get_db
from ..models import Solicitud, Convocatoria, Concesion, Beneficiario
from ..schemas import (
    EstadisticasOut, EstadisticaAnio,
    EstadisticasEpaOut, EpaAnio, TopBeneficiarioEpa, RangoImporte,
    EstadisticasEellOut, CcaaItem, ProvinciaItem, ConcentracionItem,
    EellAnioRecurrencia,
)

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("/", response_model=EstadisticasOut)
def get_estadisticas(response: Response, db: Session = Depends(get_db)):
    """
    Totales por año y tipo (EPA/EELL): conteo por estado e importe concedido.
    Usado por los gráficos de home.js y por las páginas de estadísticas.
    Cache-Control: 1 hora — los datos cambian como mucho 1-2 veces al año.
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


@router.get("/epas", response_model=EstadisticasEpaOut)
def get_estadisticas_epas(response: Response, db: Session = Depends(get_db)):
    """
    Estadísticas detalladas de EPAs: distribución de importes, media/mediana,
    beneficiarios nuevos vs recurrentes y top beneficiarios por año.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    # Todas las concesiones EPA con beneficiario y año
    rows = (
        db.query(
            Convocatoria.anio_convocatoria,
            Beneficiario.id_benef,
            Beneficiario.nombre,
            Concesion.importe,
        )
        .join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
        .join(Concesion, Concesion.id_solic == Solicitud.id_solic)
        .join(Beneficiario, Beneficiario.id_benef == Solicitud.id_benef)
        .filter(Convocatoria.tipo_convoc == "epa", Solicitud.estado == "concedida")
        .all()
    )

    # Beneficiarios únicos en todas las solicitudes EPA (no solo concedidas)
    benef_unicos = (
        db.query(func.count(distinct(Solicitud.id_benef)))
        .join(Convocatoria, Convocatoria.id_convoc == Solicitud.id_convoc)
        .filter(Convocatoria.tipo_convoc == "epa")
        .scalar()
    ) or 0

    if not rows:
        return EstadisticasEpaOut(
            importe_medio=0.0, mediana=0.0,
            beneficiarios_unicos=benef_unicos, nuevas_entidades=0,
            distribucion_importes=[], por_anio=[],
        )

    # Agrupar por año
    por_anio_raw: dict[int, list] = defaultdict(list)
    for r in rows:
        por_anio_raw[r.anio_convocatoria].append(r)

    # Primer año de concesión de cada beneficiario (para clasificar nuevos/recurrentes)
    primer_anio: dict[int, int] = {}
    for r in rows:
        if r.id_benef not in primer_anio or r.anio_convocatoria < primer_anio[r.id_benef]:
            primer_anio[r.id_benef] = r.anio_convocatoria

    # Estadísticas globales
    todos_importes = [float(r.importe) for r in rows]
    importe_medio_global = sum(todos_importes) / len(todos_importes)
    mediana_global       = median(todos_importes)

    # nuevas_entidades = beneficiarios cuya primera concesión es el año más reciente con datos
    anio_max = max(por_anio_raw.keys())
    nuevas_entidades = sum(1 for benef_id, anio in primer_anio.items() if anio == anio_max)

    # Distribución de importes en rangos
    RANGOS = [
        ("< 2.000 €",      0,      2_000),
        ("2.000–4.000 €",  2_000,  4_000),
        ("4.000–6.000 €",  4_000,  6_000),
        ("6.000–8.000 €",  6_000,  8_000),
        ("8.000–10.000 €", 8_000, 10_001),
    ]
    distribucion = [
        RangoImporte(
            rango=label,
            cantidad=sum(1 for imp in todos_importes if low <= imp < high),
        )
        for label, low, high in RANGOS
    ]

    # Estadísticas por año
    anios_out: list[EpaAnio] = []
    for anio in sorted(por_anio_raw.keys()):
        filas_anio  = por_anio_raw[anio]
        imp_anio    = [float(r.importe) for r in filas_anio]
        benef_anio  = set(r.id_benef for r in filas_anio)

        nuevos_anio      = {bid for bid in benef_anio if primer_anio.get(bid) == anio}
        recurrentes_anio = benef_anio - nuevos_anio

        # Importe acumulado por beneficiario este año (para top 10)
        acum: dict[int, dict] = {}
        for r in filas_anio:
            if r.id_benef not in acum:
                acum[r.id_benef] = {"nombre": r.nombre, "importe": 0.0}
            acum[r.id_benef]["importe"] += float(r.importe)

        top10 = sorted(acum.values(), key=lambda x: x["importe"], reverse=True)[:10]

        anios_out.append(EpaAnio(
            anio        = anio,
            media       = round(sum(imp_anio) / len(imp_anio), 2),
            mediana     = round(median(imp_anio), 2),
            nuevos      = len(nuevos_anio),
            recurrentes = len(recurrentes_anio),
            top_beneficiarios=[
                TopBeneficiarioEpa(nombre=b["nombre"], importe=round(b["importe"], 2))
                for b in top10
            ],
        ))

    return EstadisticasEpaOut(
        importe_medio        = round(importe_medio_global, 2),
        mediana              = round(mediana_global, 2),
        beneficiarios_unicos = benef_unicos,
        nuevas_entidades     = nuevas_entidades,
        distribucion_importes= distribucion,
        por_anio             = anios_out,
    )


@router.get("/eell", response_model=EstadisticasEellOut)
def get_estadisticas_eell(response: Response, db: Session = Depends(get_db)):
    """
    Estadísticas detalladas de EELL: cobertura territorial, concentración
    del importe por CCAA y provincia, ratio de exclusión, distribución por
    tramos de importe y recurrencia de entidades (nuevas vs recurrentes).
    """
    response.headers["Cache-Control"] = "public, max-age=3600"

    # Todas las solicitudes EELL
    solicitudes = (
        db.query(
            Solicitud.id_benef,
            Solicitud.estado,
            Solicitud.ccaa,
            Solicitud.provincia,
        )
        .join(Convocatoria, Convocatoria.id_convoc == Solicitud.id_convoc)
        .filter(Convocatoria.tipo_convoc == "eell")
        .all()
    )

    # Todas las concesiones EELL con datos geográficos, año y nombre
    concesiones = (
        db.query(
            Solicitud.id_benef,
            Solicitud.ccaa,
            Solicitud.provincia,
            Concesion.importe,
            Convocatoria.anio_convocatoria,
            Beneficiario.nombre,
        )
        .join(Solicitud, Solicitud.id_solic == Concesion.id_solic)
        .join(Convocatoria, Convocatoria.id_convoc == Solicitud.id_convoc)
        .join(Beneficiario, Beneficiario.id_benef == Solicitud.id_benef)
        .filter(Convocatoria.tipo_convoc == "eell", Solicitud.estado == "concedida")
        .all()
    )

    if not solicitudes:
        return EstadisticasEellOut(
            pct_ayuntamientos_con_ayuda=0.0, importe_medio=0.0,
            ratio_exclusion=0.0, ccaa_top="",
            por_ccaa=[], top_provincias=[],
            concentracion=ConcentracionItem(top_10_pct=0.0, resto_pct=100.0),
        )

    # % ayuntamientos con ayuda (de los que solicitaron, cuántos obtuvieron al menos una)
    total_solicitantes = len(set(s.id_benef for s in solicitudes))
    benef_con_ayuda    = len(set(c.id_benef for c in concesiones))
    pct_con_ayuda = (benef_con_ayuda / total_solicitantes * 100) if total_solicitantes else 0.0

    # Ratio de exclusión (excluidas + desistidas / total)
    excluidas = sum(1 for s in solicitudes if s.estado in ("excluida", "desistida"))
    ratio_exclusion = excluidas / len(solicitudes)

    # Importe medio de concesiones EELL
    importes = [float(c.importe) for c in concesiones]
    importe_medio = sum(importes) / len(importes) if importes else 0.0

    # Agregado por CCAA
    ccaa_data: dict[str, dict] = defaultdict(lambda: {"importe_total": 0.0, "num_concesiones": 0})
    for c in concesiones:
        clave = c.ccaa or "Desconocida"
        ccaa_data[clave]["importe_total"]   += float(c.importe)
        ccaa_data[clave]["num_concesiones"] += 1

    por_ccaa = sorted(
        [CcaaItem(ccaa=k, importe_total=round(v["importe_total"], 2), num_concesiones=v["num_concesiones"])
         for k, v in ccaa_data.items()],
        key=lambda x: x.importe_total, reverse=True,
    )
    ccaa_top = por_ccaa[0].ccaa if por_ccaa else ""

    # Top provincias
    prov_data: dict[str, float] = defaultdict(float)
    for c in concesiones:
        prov_data[c.provincia or "Desconocida"] += float(c.importe)

    top_provincias = sorted(
        [ProvinciaItem(provincia=k, importe_total=round(v, 2)) for k, v in prov_data.items()],
        key=lambda x: x.importe_total, reverse=True,
    )[:20]

    # Concentración: top 10% de beneficiarios vs resto del importe
    benef_importes: dict[int, float] = defaultdict(float)
    for c in concesiones:
        benef_importes[c.id_benef] += float(c.importe)

    importes_ordenados = sorted(benef_importes.values(), reverse=True)
    total_global = sum(importes_ordenados)
    n_top        = max(1, len(importes_ordenados) // 10)
    top_10_pct   = (sum(importes_ordenados[:n_top]) / total_global * 100) if total_global else 0.0

    # Distribución de importes en tramos. Las EELL manejan importes mucho
    # mayores y más dispersos que las EPA (de ~3.000 € a ~100.000 €), así
    # que los tramos son más anchos que los de /estadisticas/epas.
    RANGOS = [
        ("< 10.000 €",       0,      10_000),
        ("10.000–25.000 €",  10_000, 25_000),
        ("25.000–50.000 €",  25_000, 50_000),
        ("50.000–75.000 €",  50_000, 75_000),
        ("≥ 75.000 €",       75_000, float("inf")),
    ]
    distribucion = [
        RangoImporte(
            rango=label,
            cantidad=sum(1 for imp in importes if low <= imp < high),
        )
        for label, low, high in RANGOS
    ]

    # Recurrencia: cuántas entidades son nuevas (primera concesión ese año)
    # frente a recurrentes (ya concedidas en un año anterior). Las EELL
    # apenas repiten entre convocatorias, y ese propio hecho es el hallazgo.
    primer_anio: dict[int, int] = {}
    anios_por_benef: dict[int, set] = defaultdict(set)
    anio_benef: dict[int, set] = defaultdict(set)
    nombre_por_benef: dict[int, str] = {}
    for c in concesiones:
        anios_por_benef[c.id_benef].add(c.anio_convocatoria)
        anio_benef[c.anio_convocatoria].add(c.id_benef)
        nombre_por_benef[c.id_benef] = c.nombre
        if c.id_benef not in primer_anio or c.anio_convocatoria < primer_anio[c.id_benef]:
            primer_anio[c.id_benef] = c.anio_convocatoria

    recurrencia = []
    for anio, benefs in sorted(anio_benef.items()):
        recurrentes_ids = [b for b in benefs if primer_anio[b] != anio]
        recurrencia.append(EellAnioRecurrencia(
            anio                = anio,
            nuevas              = sum(1 for b in benefs if primer_anio[b] == anio),
            recurrentes         = len(recurrentes_ids),
            recurrentes_nombres = sorted(nombre_por_benef[b] for b in recurrentes_ids),
        ))
    entidades_repiten = sum(1 for anios in anios_por_benef.values() if len(anios) > 1)

    return EstadisticasEellOut(
        pct_ayuntamientos_con_ayuda = round(pct_con_ayuda, 1),
        importe_medio               = round(importe_medio, 2),
        ratio_exclusion             = round(ratio_exclusion, 4),
        ccaa_top                    = ccaa_top,
        por_ccaa                    = por_ccaa,
        top_provincias              = top_provincias,
        concentracion               = ConcentracionItem(
            top_10_pct = round(top_10_pct, 1),
            resto_pct  = round(100 - top_10_pct, 1),
        ),
        distribucion_importes       = distribucion,
        recurrencia_por_anio        = recurrencia,
        entidades_repiten           = entidades_repiten,
        total_entidades             = len(anios_por_benef),
    )
