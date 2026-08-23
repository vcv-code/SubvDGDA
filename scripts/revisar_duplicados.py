#!/usr/bin/env python3
"""
revisar_duplicados.py — Busca entidades que probablemente sean la misma.

Los datos vienen del BOE tal cual se publican, y ahí aparecen erratas y
variantes que hacen que una misma entidad se cuente como varias: el CIF con
dos dígitos transpuestos, el nombre en catalán un año y castellanizado al
siguiente, un año sin CIF...

Cuando eso pasa, la entidad no sale en el resumen conjunto y los recuentos de
«recurrentes» la infravaloran.

Este script NO corrige nada. Solo lista lo sospechoso para revisarlo a mano
contra fuentes oficiales (INE para municipios, registro de asociaciones para
las protectoras). Corregir un CIF sin autoridad para hacerlo sería inventar.

Uso:
    python3 scripts/revisar_duplicados.py
"""
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).parent.parent


def _cfg(*nombres, defecto):
    for n in nombres:
        v = os.environ.get(n)
        if v:
            return v
    return defecto


# Provincia según los dos dígitos que siguen a la letra en el CIF de un
# ayuntamiento (P + 2 dígitos de provincia + 3 de municipio + control).
PROVINCIAS = {
    '01': ('Álava', 'País Vasco'),            '02': ('Albacete', 'Castilla-La Mancha'),
    '03': ('Alicante', 'Comunidad Valenciana'), '04': ('Almería', 'Andalucía'),
    '05': ('Ávila', 'Castilla y León'),       '06': ('Badajoz', 'Extremadura'),
    '07': ('Baleares', 'Illes Balears'),      '08': ('Barcelona', 'Cataluña'),
    '09': ('Burgos', 'Castilla y León'),      '10': ('Cáceres', 'Extremadura'),
    '11': ('Cádiz', 'Andalucía'),             '12': ('Castellón', 'Comunidad Valenciana'),
    '13': ('Ciudad Real', 'Castilla-La Mancha'), '14': ('Córdoba', 'Andalucía'),
    '15': ('A Coruña', 'Galicia'),            '16': ('Cuenca', 'Castilla-La Mancha'),
    '17': ('Girona', 'Cataluña'),             '18': ('Granada', 'Andalucía'),
    '19': ('Guadalajara', 'Castilla-La Mancha'), '20': ('Gipuzkoa', 'País Vasco'),
    '21': ('Huelva', 'Andalucía'),            '22': ('Huesca', 'Aragón'),
    '23': ('Jaén', 'Andalucía'),              '24': ('León', 'Castilla y León'),
    '25': ('Lleida', 'Cataluña'),             '26': ('La Rioja', 'La Rioja'),
    '27': ('Lugo', 'Galicia'),                '28': ('Madrid', 'Comunidad de Madrid'),
    '29': ('Málaga', 'Andalucía'),            '30': ('Murcia', 'Región de Murcia'),
    '31': ('Navarra', 'Navarra'),             '32': ('Ourense', 'Galicia'),
    '33': ('Asturias', 'Asturias'),           '34': ('Palencia', 'Castilla y León'),
    '35': ('Las Palmas', 'Canarias'),         '36': ('Pontevedra', 'Galicia'),
    '37': ('Salamanca', 'Castilla y León'),   '38': ('S. C. Tenerife', 'Canarias'),
    '39': ('Cantabria', 'Cantabria'),         '40': ('Segovia', 'Castilla y León'),
    '41': ('Sevilla', 'Andalucía'),           '42': ('Soria', 'Castilla y León'),
    '43': ('Tarragona', 'Cataluña'),          '44': ('Teruel', 'Aragón'),
    '45': ('Toledo', 'Castilla-La Mancha'),   '46': ('Valencia', 'Comunidad Valenciana'),
    '47': ('Valladolid', 'Castilla y León'),  '48': ('Bizkaia', 'País Vasco'),
    '49': ('Zamora', 'Castilla y León'),      '50': ('Zaragoza', 'Aragón'),
    '51': ('Ceuta', 'Ceuta'),                 '52': ('Melilla', 'Melilla'),
}

# Palabras que no distinguen a una entidad de otra: aparecen en casi todas y
# varían de forma (idioma, abreviatura) sin cambiar de quién se habla.
RUIDO = {
    'ASOCIACION', 'ASSOCIACIO', 'ASOC', 'ASSOC', 'ACAD',
    'PROTECTORA', 'PROTECTORAS', 'PROTECCIO', 'PROTECCION',
    'ANIMALES', 'ANIMALS', 'ANIMAL',
    'SOCIEDAD', 'SOCIETAT', 'FUNDACION', 'FUNDACIO',
    'AYUNTAMIENTO', 'AJUNTAMENT', 'CONCELLO', 'UDALA', 'AYTO',
    'DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'Y', 'I', 'E',
}


def clave_ccaa(nombre):
    """Reduce el nombre de una comunidad a algo comparable.

    Las fuentes usan tanto la forma corta como la oficial —«Asturias» y
    «Principado de Asturias», «Navarra» y «Comunidad Foral de Navarra»— y
    compararlas literalmente daba 53 avisos falsos de 53.
    """
    t = sin_tildes(nombre or '').upper()
    for sobra in ('PRINCIPADO DE', 'COMUNIDAD FORAL DE', 'CIUDAD AUTONOMA DE',
                  'COMUNIDAD DE', 'COMUNIDAD', 'REGION DE', 'ISLAS', 'ILLES',
                  'PAIS', 'LA ', 'EL '):
        t = t.replace(sobra, ' ')
    return ' '.join(t.split())


def sin_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def normalizar(nombre):
    """Reduce el nombre a lo que de verdad identifica a la entidad.

    Quita tildes, colapsa consonantes dobles —«Associació» y «Asociación» solo
    se distinguen en eso— y retira las palabras genéricas que aparecen en casi
    todos los nombres. Lo que queda es el núcleo comparable.
    """
    t = sin_tildes(nombre).upper()
    t = re.sub(r'[^A-Z0-9 ]', ' ', t)
    t = re.sub(r'([A-Z])\1+', r'\1', t)          # SS → S, LL → L, RR → R
    palabras = [p for p in t.split() if p and p not in RUIDO]
    return ' '.join(sorted(palabras))


def diferencia_cif(a, b):
    """Describe en qué se parecen dos CIF, si es que se parecen."""
    if not a or not b or len(a) != len(b):
        return None
    distintos = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(distintos) == 1:
        return f"un solo carácter distinto (posición {distintos[0] + 1}: {a[distintos[0]]}/{b[distintos[0]]})"
    if len(distintos) == 2:
        i, j = distintos
        if a[i] == b[j] and a[j] == b[i]:
            return f"dos dígitos transpuestos ({a[i]} y {a[j]})"
        return "dos caracteres distintos"
    return None


def cargar_env():
    """Carga docker/.env en el entorno.

    Hace falta porque este script se ejecuta desde el anfitrión, no dentro del
    contenedor: `backend/app/db.py` ya apunta a 127.0.0.1:3307 por defecto,
    pero la contraseña real vive en el .env y no está en el entorno.
    """
    env = RAIZ / 'docker' / '.env'
    if not env.exists():
        sys.exit("ERROR: falta docker/.env — ejecuta 'bash install.sh'.")
    for linea in env.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        os.environ.setdefault(clave.strip(), valor.strip())


def cargar():
    """Lee entidades y sus años desde la base de datos."""
    cargar_env()
    sys.path.insert(0, str(RAIZ))
    from backend.app.db import SessionLocal
    from backend.app.models import Beneficiario, Solicitud, Convocatoria

    db = SessionLocal()
    try:
        filas = (
            db.query(
                Beneficiario.id_benef, Beneficiario.cif, Beneficiario.nombre,
                Beneficiario.tipo_benef, Convocatoria.anio_convocatoria,
                Convocatoria.tipo_convoc, Solicitud.ccaa,
            )
            .join(Solicitud, Solicitud.id_benef == Beneficiario.id_benef)
            .join(Convocatoria, Convocatoria.id_convoc == Solicitud.id_convoc)
            .all()
        )
    finally:
        db.close()

    entidades = {}
    for id_b, cif, nombre, tipo_b, anio, tipo_c, ccaa in filas:
        e = entidades.setdefault(id_b, {
            'cif': cif, 'nombre': nombre, 'tipo': tipo_b,
            'anios': set(), 'ccaas': set(), 'solicitudes': 0,
        })
        e['anios'].add(anio)
        if ccaa:
            e['ccaas'].add(ccaa)
        e['solicitudes'] += 1
    return entidades


def posibles_duplicados(entidades):
    """Entidades del MISMO tipo cuyo nombre normalizado coincide.

    Se agrupa por tipo a propósito: al retirar las palabras genéricas, «Asociación
    Protectora de Berja» y «Ayuntamiento de Berja» se reducen ambas a «BERJA» y
    parecerían la misma. Son entidades distintas del mismo pueblo, y sin esta
    separación la lista se llenaba de avisos falsos.

    También se descartan las claves demasiado cortas: un nombre que solo contiene
    palabras genéricas se queda casi vacío al normalizar y agruparía cosas sin
    relación.
    """
    grupos = defaultdict(list)
    for id_b, e in entidades.items():
        clave = normalizar(e['nombre'])
        if len(clave) < 5:
            continue
        grupos[(e['tipo'], clave)].append((id_b, e))
    return {k: v for k, v in grupos.items() if len(v) > 1}


def sin_cif(entidades):
    return [(i, e) for i, e in entidades.items() if not e['cif']]


def provincia_incoherente(entidades):
    """Ayuntamientos cuyo CIF apunta a una comunidad distinta de la declarada."""
    fuera = []
    for i, e in entidades.items():
        cif = e['cif'] or ''
        if not cif.upper().startswith('P') or len(cif) < 3:
            continue
        datos = PROVINCIAS.get(cif[1:3])
        if not datos:
            continue
        prov, ccaa_cif = datos
        for ccaa in e['ccaas']:
            if clave_ccaa(ccaa) != clave_ccaa(ccaa_cif):
                fuera.append((i, e, prov, ccaa_cif, ccaa))
                break
    return fuera


# Fichero del INE con los 8.132 municipios y su provincia. Es OPCIONAL: sin él
# el resto del informe funciona igual. Se descarga de www.ine.es (Relación de
# municipios y códigos por comunidades autónomas y provincias) y NO se versiona.
INE_MUNICIPIOS = Path(os.environ.get(
    "INE_MUNICIPIOS", RAIZ / "data/raw/ine/diccionario_municipios.xlsx"))


def municipios_por_provincia():
    """Nombre de municipio normalizado → provincias del INE donde existe.

    IMPORTANTE: no se usa para traducir el CIF a un nombre. Los tres dígitos de
    municipio del CIF los asigna Hacienda y NO son el código del INE —se
    comprobó con cuatro casos verificados y solo coincidían dos—. Lo que sí es
    fiable son los dos dígitos de provincia, así que la comprobación va al
    revés: se busca el nombre en el INE y se mira si alguna de sus provincias
    coincide con la del CIF.
    """
    if not INE_MUNICIPIOS.exists():
        return None
    try:
        import openpyxl
    except ImportError:
        return None
    wb = openpyxl.load_workbook(INE_MUNICIPIOS, read_only=True)
    idx = defaultdict(set)
    for f in wb.active.iter_rows(min_row=3, values_only=True):
        if not f or not f[1] or not f[4]:
            continue
        cpro, bruto = str(f[1]).zfill(2), str(f[4])
        variantes = [bruto]
        if ',' in bruto:                       # «Cuervo de Sevilla, El»
            base, art = [x.strip() for x in bruto.split(',', 1)]
            variantes += [f"{art} {base}", base]
        for v in variantes:
            for parte in v.split('/'):         # nombres bilingües
                idx[sin_tildes(parte).upper().strip()].add(cpro)
    wb.close()
    return idx


def main():
    entidades = cargar()
    print(f"Entidades analizadas: {len(entidades)}\n")

    dups = posibles_duplicados(entidades)
    print("═" * 78)
    print(f"1. POSIBLES DUPLICADOS — mismo nombre, CIF distinto  ({len(dups)} grupos)")
    print("═" * 78)
    for clave in sorted(dups, key=lambda k: (k[0], k[1])):
        grupo = sorted(dups[clave], key=lambda x: (x[1]['cif'] or ''))
        print()
        for _, e in grupo:
            anios = ', '.join(str(a) for a in sorted(e['anios']))
            print(f"  {(e['cif'] or 'SIN CIF'):<12} {e['nombre'][:46]:<48} {anios}")
        cifs = [e['cif'] for _, e in grupo if e['cif']]
        for a, b in zip(cifs, cifs[1:]):
            d = diferencia_cif(a, b)
            if d:
                print(f"  {'':12} → {d}")

    faltan = sin_cif(entidades)
    print()
    print("═" * 78)
    print(f"2. ENTIDADES SIN CIF  ({len(faltan)})")
    print("═" * 78)
    for _, e in sorted(faltan, key=lambda x: x[1]['nombre']):
        print(f"  {e['nombre'][:52]:<54} {', '.join(str(a) for a in sorted(e['anios']))}")

    incoh = provincia_incoherente(entidades)
    print()
    print("═" * 78)
    print(f"3. AYUNTAMIENTOS: EL CIF NO CUADRA CON LA COMUNIDAD  ({len(incoh)})")
    print("═" * 78)
    print("  El CIF de un ayuntamiento lleva la provincia en sus dos primeros")
    print("  dígitos. Si no coincide con la comunidad declarada, uno de los dos")
    print("  campos está mal — o el nombre corresponde a otro municipio.\n")
    for _, e, prov, ccaa_cif, ccaa in sorted(incoh, key=lambda x: x[1]['nombre']):
        print(f"  {e['nombre'][:40]:<42} {e['cif']}")
        print(f"  {'':42} CIF dice {prov} ({ccaa_cif}) · el dato dice {ccaa}")

    ine = municipios_por_provincia()
    print()
    print("═" * 78)
    if ine is None:
        print("4. MUNICIPIOS MAL ETIQUETADOS — no comprobado")
        print("═" * 78)
        print(f"  Falta el fichero del INE en {INE_MUNICIPIOS}")
        print("  (o la librería openpyxl). Es opcional: sin él no se puede")
        print("  comprobar si el nombre de un municipio cuadra con la provincia")
        print("  de su CIF, que es lo que detecta los mal etiquetados.")
    else:
        PREFIJOS = ('AYUNTAMIENTO DE ', 'AJUNTAMENT DE ', 'CONCELLO DE ', 'AYUNTAMIENTO ',
                    'AJUNTAMENT ', 'CONCELLO ', 'AYTO DE ', 'AYTO ', 'AGRUPACION DEL ',
                    'AGRUPACION DE ', 'AGRUPACION ', 'MANCOMUNIDAD DE ', 'MANCOMUNIDAD ')
        sospechosos, sin_hallar = [], 0
        for _, e in entidades.items():
            cif = (e['cif'] or '').upper()
            if e['tipo'] != 'entidad_local' or not re.match(r'^P\d{7}', cif):
                continue
            nombre = sin_tildes(e['nombre']).upper()
            for pre in PREFIJOS:
                nombre = nombre.replace(pre, ' ')
            nombre = ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', nombre).split())
            provs = ine.get(nombre)
            if not provs:
                sin_hallar += 1
                continue
            if cif[1:3] not in provs:
                sospechosos.append((e, cif[1:3], sorted(provs)))

        print(f"4. MUNICIPIOS MAL ETIQUETADOS  ({len(sospechosos)} sospechosos)")
        print("═" * 78)
        print(f"  Nombre no encontrado en el INE (abreviado o agrupación): {sin_hallar}\n")
        for e, cpro, provs in sorted(sospechosos, key=lambda x: x[0]['nombre']):
            p_cif = PROVINCIAS.get(cpro, ('?', '?'))[0]
            otras = ', '.join(PROVINCIAS.get(x, ('?',))[0] for x in provs)
            print(f"  {e['cif']}  {e['nombre'][:38]:<40}")
            print(f"  {'':12}  CIF dice {p_cif} · el municipio está en {otras}")
        print()
        print("  Ojo: un nombre abreviado da falso positivo (p. ej. «Burguillos»")
        print("  por «Burguillos de Toledo»), y hay municipios que cambiaron de")
        print("  provincia conservando su CIF antiguo, como Gátova.")

    print()
    print("─" * 78)
    print("Nada de esto se corrige automáticamente: hay que comprobarlo contra")
    print("fuentes oficiales (INE para municipios, registro de asociaciones para")
    print("las protectoras) antes de tocar un solo dato.")


if __name__ == '__main__':
    main()
