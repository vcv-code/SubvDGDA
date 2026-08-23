-- =============================================================================
-- Migración 2026-08-23 — periodo subvencionable y erratas del origen
-- =============================================================================
-- Lleva una base de datos ya existente del estado v1.6 al de esta versión.
--
-- POR QUÉ HACE FALTA. `modelo-fisico.sql` está montado en
-- /docker-entrypoint-initdb.d/, y MariaDB solo ejecuta eso cuando el directorio
-- de datos está VACÍO. En un despliegue con datos no se vuelve a ejecutar
-- nunca, así que las columnas nuevas no aparecerían solas. Y el modelo ORM sí
-- las mapea: sin esta migración, la API pediría `SELECT ... periodo_anio ...`
-- contra una tabla que no las tiene (error 1054) y la portada daría un 500.
--
-- Tampoco vale `cargar_dataset`: es ADITIVO, inserta lo que falta pero no
-- reescribe filas existentes, así que no corregiría los nombres ni fusionaría
-- las entidades duplicadas.
--
-- NO USAR `reset-db` EN PRODUCCIÓN. Borraría la cuenta de administración y las
-- `fecha_fin_plazo`, que no están en el dataset y hay que rellenar a mano.
--
-- ES IDEMPOTENTE: se puede lanzar dos veces sin estropear nada. Las columnas
-- usan IF NOT EXISTS, los UPDATE fijan valores absolutos y las fusiones
-- comprueban antes si ya se hicieron.
--
-- CÓMO LANZARLA (con backup previo, desde /opt/subvdgda):
--   bash scripts/backup_db.sh
--   cd docker && docker compose exec -T db \
--       mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
--       < ../scripts/migraciones/2026-08-23_periodo_y_erratas.sql
--
-- Ensayada contra una réplica del esquema y los datos de v1.6 antes de
-- escribirla aquí.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Columnas nuevas en `convocatorias`
-- -----------------------------------------------------------------------------
-- El año de gasto que financia una convocatoria NO es el suyo: las EPA de
-- 2021-2024 y todas las EELL pagan gastos del año siguiente.

ALTER TABLE convocatorias
    ADD COLUMN IF NOT EXISTS periodo_anio  VARCHAR(16) NULL
        COMMENT 'Año o años de gasto que financia la convocatoria. NO coincide con anio_convocatoria. NULL si el extracto del BOE no lo declara',
    ADD COLUMN IF NOT EXISTS periodo_matiz VARCHAR(40) NULL
        COMMENT 'Precisión cuando no es el año completo, p. ej. «1.er semestre». NULL si cubre el año entero';

-- -----------------------------------------------------------------------------
-- 2. Periodo subvencionable de cada convocatoria
-- -----------------------------------------------------------------------------
-- Transcrito del apartado «Objeto» del extracto de cada convocatoria en el BOE.
-- Espejo de `_PERIODO_SUBVENCIONABLE` en scripts/data_processing/cargar_dataset.py.

UPDATE convocatorias SET periodo_meses=12, periodo_anio='2022',    periodo_matiz=NULL             WHERE tipo_convoc='epa'  AND anio_convocatoria=2021;
UPDATE convocatorias SET periodo_meses=12, periodo_anio='2023',    periodo_matiz=NULL             WHERE tipo_convoc='epa'  AND anio_convocatoria=2022;
UPDATE convocatorias SET periodo_meses=6,  periodo_anio='2024',    periodo_matiz='1.er semestre'  WHERE tipo_convoc='epa'  AND anio_convocatoria=2023;
UPDATE convocatorias SET periodo_meses=6,  periodo_anio='2024',    periodo_matiz='2.º semestre'   WHERE tipo_convoc='epa'  AND anio_convocatoria=2024;
UPDATE convocatorias SET periodo_meses=12, periodo_anio='2025',    periodo_matiz=NULL             WHERE tipo_convoc='epa'  AND anio_convocatoria=2025;
UPDATE convocatorias SET periodo_meses=12, periodo_anio='2026',    periodo_matiz=NULL             WHERE tipo_convoc='epa'  AND anio_convocatoria=2026;

-- OJO: la EELL de 2023 NO fue anual. Su extracto fija «entre el 1 de octubre de
-- 2023 y el 31 de marzo del año 2024»: seis meses. Constaba como 12.
UPDATE convocatorias SET periodo_meses=6,  periodo_anio='2023–24', periodo_matiz='oct a mar'      WHERE tipo_convoc='eell' AND anio_convocatoria=2023;
UPDATE convocatorias SET periodo_meses=12, periodo_anio='2025',    periodo_matiz=NULL             WHERE tipo_convoc='eell' AND anio_convocatoria=2024;
UPDATE convocatorias SET periodo_meses=12, periodo_anio='2026',    periodo_matiz=NULL             WHERE tipo_convoc='eell' AND anio_convocatoria=2025;
-- La EELL de 2026 no declara ventana de gasto en su extracto: se queda en NULL
-- a propósito. Deducirla por la pauta de años anteriores sería inventar.
UPDATE convocatorias SET periodo_meses=12, periodo_anio=NULL,      periodo_matiz=NULL             WHERE tipo_convoc='eell' AND anio_convocatoria=2026;

-- -----------------------------------------------------------------------------
-- 3. Municipios con el nombre mal en el BOE
-- -----------------------------------------------------------------------------
-- El CIF sí era correcto —por eso el mapa y las estadísticas por comunidad ya
-- salían bien—, solo el nombre estaba equivocado. Verificado contra las webs
-- municipales y el diccionario de municipios del INE.
-- Casavieja (Ávila, P0505400B) y Castilforte (Guadalajara, P1909200F) existen y
-- NO se tocan: tienen su propio CIF y sus propias solicitudes.

UPDATE beneficiarios SET nombre='AYUNTAMIENTO DE CARLET'               WHERE cif='P4608700C';
UPDATE beneficiarios SET nombre='AYUNTAMIENTO DE CARRIÓN DE CALATRAVA' WHERE cif='P1303100J';

-- -----------------------------------------------------------------------------
-- 4. Entidades partidas en dos fichas por una errata del CIF
-- -----------------------------------------------------------------------------
-- Se mueven las solicitudes a la ficha buena y se borra la duplicada. El
-- procedimiento es el mismo para las cinco, así que va en un bucle: por cada
-- par (CIF erróneo, CIF bueno) reasigna y elimina, solo si ambas fichas existen.
--
-- Fuentes de cada corrección:
--   G72307358 -> G72296254  BOE-A-2023-13752, corrección de errores oficial
--   G16734071 -> G16737041  BDNS, concesión de 2022; y 3 años frente a 1
--   B54999156 -> G54999156  Registro de Asociaciones de Alicante: una
--                           asociación no lleva NIF con «B», de sociedad limitada
--   G56705338 -> G56725328  SIN fuente externa. Se adopta el de 2025 por ser la
--                           publicación más reciente. Decisión revisable.
--   (sin CIF) -> G67811000  LAS ALMAS DE COCOA: su registro de 2021 salió sin
--                           CIF; lo confirma la BDNS con la concesión de 2022

DROP PROCEDURE IF EXISTS fusionar_beneficiarios;
DELIMITER //
CREATE PROCEDURE fusionar_beneficiarios(IN cif_malo VARCHAR(20), IN cif_bueno VARCHAR(20))
BEGIN
    DECLARE id_malo  INT DEFAULT NULL;
    DECLARE id_bueno INT DEFAULT NULL;

    SELECT id_benef INTO id_malo  FROM beneficiarios WHERE cif = cif_malo  LIMIT 1;
    SELECT id_benef INTO id_bueno FROM beneficiarios WHERE cif = cif_bueno LIMIT 1;

    -- Si la ficha errónea ya no está, la fusión se hizo antes: no hay nada que
    -- hacer. Eso es lo que hace idempotente a este paso.
    IF id_malo IS NOT NULL AND id_bueno IS NOT NULL THEN
        UPDATE solicitudes         SET id_benef = id_bueno WHERE id_benef = id_malo;
        UPDATE agrupacion_miembros SET id_benef = id_bueno WHERE id_benef = id_malo;
        UPDATE agrupaciones        SET id_represent = id_bueno WHERE id_represent = id_malo;
        DELETE FROM beneficiarios WHERE id_benef = id_malo;
    END IF;
END //
DELIMITER ;

CALL fusionar_beneficiarios('G72307358', 'G72296254');
CALL fusionar_beneficiarios('G16734071', 'G16737041');
CALL fusionar_beneficiarios('B54999156', 'G54999156');
CALL fusionar_beneficiarios('G56705338', 'G56725328');

DROP PROCEDURE fusionar_beneficiarios;

-- LAS ALMAS DE COCOA va aparte: la ficha sobrante no tiene CIF, así que se
-- localiza por nombre. Se comprueba que la ficha con CIF exista antes de mover
-- nada, para no dejar solicitudes huérfanas si algo cambiara en el origen.
UPDATE solicitudes s
   JOIN beneficiarios malo  ON malo.id_benef = s.id_benef
                           AND malo.cif IS NULL
                           AND malo.nombre = 'LAS ALMAS DE COCOA'
   JOIN beneficiarios bueno ON bueno.cif = 'G67811000'
   SET s.id_benef = bueno.id_benef;

DELETE FROM beneficiarios
 WHERE cif IS NULL
   AND nombre = 'LAS ALMAS DE COCOA'
   AND EXISTS (SELECT 1 FROM (SELECT 1 FROM beneficiarios WHERE cif='G67811000') x);

-- -----------------------------------------------------------------------------
-- 5. Nombre único para las entidades fusionadas
-- -----------------------------------------------------------------------------
-- Traían dos grafías, una por cada ficha. Se fija la mayoritaria para que la
-- ficha no cambie de nombre según el año que se mire.

UPDATE beneficiarios SET nombre='ASSOCIACIÓ GAT I CUA'            WHERE cif='G16737041';
UPDATE beneficiarios SET nombre='ASOCIACIÓN "GATOS DE EL PUERTO"' WHERE cif='G72296254';
