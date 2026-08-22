from collections import defaultdict
from statistics import median

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct

from ..db import get_db
from ..models import Solicitud, Convocatoria, Concesion, Beneficiario, CausaExclusion
from ..schemas import (
    EstadisticasOut, EstadisticaAnio, UmbralAnio, UmbralLinea,
    EstadisticasEpaOut, EpaAnio, TopBeneficiarioEpa, RangoImporte,
    EstadisticasEellOut, CcaaItem, ProvinciaItem, ConcentracionItem,
    EellAnioRecurrencia, ExclusionesStats, ExclusionAnio, CausaFrecuente,
    ResumenTablaOut, ResumenFilaTabla,
)

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


# ──────────────────────────────────────────────
# RESUMEN POR CONVOCATORIA (tabla)
# Agregación pública por (tipo, año): recuento por estado + importe concedido.
# La usan la home (pública) y /privado/resumen-tabla (misma lógica, sin duplicar).
# ──────────────────────────────────────────────

def construir_resumen_tabla(db: Session) -> ResumenTablaOut:
    filas = []
    total_global = concedidas_total = 0
    importe_global = 0.0

    convocatorias = db.query(Convocatoria).order_by(
        Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria
    ).all()

    for conv in convocatorias:
        solicitudes = db.query(Solicitud).filter(Solicitud.id_convoc == conv.id_convoc).all()
        total    = len(solicitudes)
        conced   = sum(1 for s in solicitudes if s.estado == "concedida")
        no_benef = sum(1 for s in solicitudes if s.estado == "no_beneficiaria")
        excl     = sum(1 for s in solicitudes if s.estado == "excluida")
        desist   = sum(1 for s in solicitudes if s.estado == "desistida")

        ids_conced = [s.id_solic for s in solicitudes if s.estado == "concedida"]
        importe = 0.0
        if ids_conced:
            concesiones = db.query(Concesion).filter(Concesion.id_solic.in_(ids_conced)).all()
            importe = float(sum(c.importe for c in concesiones if c.importe))

        filas.append(ResumenFilaTabla(
            tipo=conv.tipo_convoc,
            anio=conv.anio_convocatoria,
            total=total,
            concedidas=conced,
            no_beneficiarias=no_benef,
            excluidas=excl,
            desistidas=desist,
            importe_total=round(importe, 2),
        ))
        total_global     += total
        concedidas_total += conced
        importe_global   += importe

    return ResumenTablaOut(
        filas=filas,
        total_global=total_global,
        concedidas_total=concedidas_total,
        importe_global=round(importe_global, 2),
    )


@router.get("/resumen-convocatorias", response_model=ResumenTablaOut)
def resumen_convocatorias(response: Response, db: Session = Depends(get_db)):
    """Tabla resumen de solicitudes por tipo y año (recuento por estado + importe).
    Pública: se muestra al final de la home. Cache-Control 1 h."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return construir_resumen_tabla(db)


# ──────────────────────────────────────────────
# EXCLUSIONES (compartido por /epas y /eell)
# ──────────────────────────────────────────────

def _stats_exclusiones(db: Session, tipo: str, top_n: int = 8) -> ExclusionesStats:
    """Bloque de exclusiones para las páginas de estadísticas:

    - `por_anio`: nº de excluidas por año (comparable entre años).
    - `causas_frecuentes`: top de causas SOLO del último año con exclusiones.
      No se mezclan años porque cada convocatoria usa su propia numeración
      (el "5" de 2023 no es el "5" de 2025). El motivo sale del catálogo
      `causas_exclusion`; una solicitud con varias causas ("2;6.a") suma
      en cada una de ellas.
    """
    filas = (
        db.query(Convocatoria.anio_convocatoria, Solicitud.causa_exclusion)
        .join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
        .filter(Convocatoria.tipo_convoc == tipo, Solicitud.estado == "excluida")
        .all()
    )
    if not filas:
        return ExclusionesStats()

    por_anio: dict[int, int] = defaultdict(int)
    for anio, _ in filas:
        por_anio[anio] += 1

    ultimo = max(por_anio)

    # Frecuencia de cada código en el último año
    conteo: dict[str, int] = defaultdict(int)
    for anio, causa in filas:
        if anio != ultimo or not causa:
            continue
        for codigo in causa.split(";"):
            if codigo:
                conteo[codigo] += 1

    # Resolver código → motivo con el catálogo de ese (tipo, año)
    leyenda = {
        c.codigo: c.motivo
        for c in db.query(CausaExclusion)
                   .filter(CausaExclusion.tipo_convoc == tipo, CausaExclusion.anio == ultimo)
    }

    frecuentes = sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]

    return ExclusionesStats(
        por_anio=[ExclusionAnio(anio=a, total=t) for a, t in sorted(por_anio.items())],
        causas_anio=ultimo,
        causas_frecuentes=[
            CausaFrecuente(codigo=cod, motivo=leyenda.get(cod, ""), total=tot)
            for cod, tot in frecuentes
        ],
    )


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

    # ── Umbrales de puntuación (corte de concesión por año) ──
    # "Hubo corte" cuando existen no_beneficiarias: entidades admitidas que se
    # quedaron sin subvención por puntuación (presupuesto agotado). Si no las
    # hay, todas las admitidas obtuvieron ayuda (sin corte). El umbral es la
    # puntuación mínima entre las concedidas; para EPA con línea (2024+) se da
    # por línea, porque cada línea tiene su propio presupuesto y su propio corte.
    con_corte = {
        (t, a) for (t, a) in db.query(
            Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria
        ).join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
         .filter(Solicitud.estado == "no_beneficiaria").distinct().all()
    }

    punt_rows = (
        db.query(
            Convocatoria.tipo_convoc, Convocatoria.anio_convocatoria,
            Concesion.linea, Solicitud.puntuacion,
        )
        .join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
        .join(Concesion, Concesion.id_solic == Solicitud.id_solic)
        .filter(Solicitud.estado == "concedida", Solicitud.puntuacion.isnot(None))
        .all()
    )

    glob: dict[tuple, list] = defaultdict(list)
    por_linea: dict[tuple, dict] = defaultdict(lambda: defaultdict(list))
    for r in punt_rows:
        clave = (r.tipo_convoc, r.anio_convocatoria)
        glob[clave].append(float(r.puntuacion))
        if r.linea:
            por_linea[clave][r.linea].append(float(r.puntuacion))

    umbrales = []
    for (tipo, anio) in sorted(glob.keys()):
        if (tipo, anio) not in con_corte:
            umbrales.append(UmbralAnio(tipo=tipo, anio=anio, hubo_corte=False))
        elif tipo == "epa" and por_linea[(tipo, anio)]:
            umbrales.append(UmbralAnio(
                tipo=tipo, anio=anio, hubo_corte=True,
                por_linea=[
                    UmbralLinea(linea=l, umbral=round(min(v), 2))
                    for l, v in sorted(por_linea[(tipo, anio)].items())
                ],
            ))
        else:
            umbrales.append(UmbralAnio(
                tipo=tipo, anio=anio, hubo_corte=True,
                umbral=round(min(glob[(tipo, anio)]), 2),
            ))

    return EstadisticasOut(
        por_anio         = por_anio,
        total_registros  = sum(f.total for f in filas),
        total_concedidas = sum(f.concedidas for f in filas),
        importe_global   = sum(float(f.importe_total) for f in filas),
        entidades_unicas = entidades_unicas,
        umbrales         = umbrales,
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

    # Solicitudes presentadas y concedidas por año. Va aparte de la consulta
    # principal porque aquella parte de `concesiones` y aquí hacen falta TODAS
    # las solicitudes, concedidas o no: sin el denominador no hay tasa.
    conteos = dict()
    for anio, total, concedidas in (
        db.query(
            Convocatoria.anio_convocatoria,
            func.count(Solicitud.id_solic),
            func.sum(case((Solicitud.estado == "concedida", 1), else_=0)),
        )
        .join(Solicitud, Solicitud.id_convoc == Convocatoria.id_convoc)
        .filter(Convocatoria.tipo_convoc == "epa")
        .group_by(Convocatoria.anio_convocatoria)
        .all()
    ):
        conteos[anio] = (int(total or 0), int(concedidas or 0))

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

        total_anio, concedidas_anio = conteos.get(anio, (0, 0))

        anios_out.append(EpaAnio(
            anio        = anio,
            media       = round(sum(imp_anio) / len(imp_anio), 2),
            mediana     = round(median(imp_anio), 2),
            nuevos      = len(nuevos_anio),
            recurrentes = len(recurrentes_anio),
            solicitudes = total_anio,
            concedidas  = concedidas_anio,
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
        exclusiones          = _stats_exclusiones(db, "epa"),
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
        exclusiones                 = _stats_exclusiones(db, "eell"),
    )
