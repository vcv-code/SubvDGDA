-- ============================================================
-- Modelo físico: Análisis de subvenciones DGDA
-- Base de datos: bdns_dgda
-- ============================================================

CREATE DATABASE IF NOT EXISTS bdns_dgda
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE bdns_dgda;

-- ------------------------------------------------------------
-- CONVOCATORIAS
-- Una fila por convocatoria anual (EPA y EELL son separadas)
-- ------------------------------------------------------------
CREATE TABLE convocatorias (
    id_convoc          INT          NOT NULL AUTO_INCREMENT,
    num_convoc         VARCHAR(50)  NULL                    COMMENT 'Número oficial de convocatoria BDNS',
    titulo_convoc      VARCHAR(255) NOT NULL                COMMENT 'Descripción/título de la convocatoria',
    tipo_convoc        ENUM('epa','eell') NOT NULL          COMMENT 'epa = protectoras, eell = entidades locales',
    anio_convocatoria  INT          NOT NULL                COMMENT 'Año de la convocatoria (2021-2025)',
    fecha_convocatoria DATE         NULL                    COMMENT 'Fecha de publicación de la convocatoria',
    fecha_resolucion   DATE         NULL                    COMMENT 'Fecha de resolución definitiva',
    periodo_meses      TINYINT      NOT NULL DEFAULT 12     COMMENT 'Duración del periodo subvencionable en meses. EPA 2023 y 2024 = 6; resto = 12',
    PRIMARY KEY (id_convoc)
);

-- ------------------------------------------------------------
-- BENEFICIARIOS
-- Entidades que presentan solicitudes (asociaciones o ayuntamientos)
-- ------------------------------------------------------------
CREATE TABLE beneficiarios (
    id_benef    INT          NOT NULL AUTO_INCREMENT,
    cif         VARCHAR(20)  NULL                          COMMENT 'CIF o NIF de la entidad',
    nombre      VARCHAR(255) NOT NULL                      COMMENT 'Nombre completo de la entidad',
    tipo_benef  ENUM('asociacion','entidad_local') NOT NULL COMMENT 'Tipo de entidad beneficiaria',
    PRIMARY KEY (id_benef),
    UNIQUE KEY uq_cif (cif)
);

-- ------------------------------------------------------------
-- SOLICITUDES
-- Una fila por solicitud presentada en una convocatoria
-- Incluye TODOS los estados, tanto aprobadas como no
-- ------------------------------------------------------------
CREATE TABLE solicitudes (
    id_solic       INT              NOT NULL AUTO_INCREMENT,
    id_convoc      INT              NOT NULL,
    id_benef       INT              NOT NULL,
    num_expediente VARCHAR(50)      NULL                   COMMENT 'Número de expediente oficial. NULL si no consta en el BOE',
    puntuacion     DECIMAL(5,2)     NULL                   COMMENT 'Puntuación obtenida en la evaluación',
    estado         ENUM(
                     'concedida',
                     'no_beneficiaria',
                     'excluida',
                     'desistida'
                   ) NOT NULL                             COMMENT 'no_beneficiaria = admitida pero fuera del cupo (EELL todos los años; EPA desde 2024)',
    PRIMARY KEY (id_solic),
    -- Clave compuesta: el mismo num_expediente puede aparecer en convocatorias distintas
    -- (entidades que desistieron un año y volvieron al siguiente).
    UNIQUE KEY uq_expediente (num_expediente, id_convoc),
    CONSTRAINT fk_solic_convoc FOREIGN KEY (id_convoc) REFERENCES convocatorias (id_convoc),
    CONSTRAINT fk_solic_benef  FOREIGN KEY (id_benef)  REFERENCES beneficiarios  (id_benef)
);

-- ------------------------------------------------------------
-- CONCESIONES
-- Solo existen cuando estado = 'concedida' e importe > 0
-- Las no_beneficiaria, excluidas y desistidas NO generan fila aquí
-- ------------------------------------------------------------
CREATE TABLE concesiones (
    id_conces  INT              NOT NULL AUTO_INCREMENT,
    id_solic   INT              NOT NULL,
    importe    DECIMAL(12,2)    NOT NULL DEFAULT 0.00      COMMENT 'Importe concedido en euros',
    linea      ENUM(
                 'colonias_felinas',
                 'proteccion_animal',
                 'eell'
               ) NULL                                      COMMENT 'Línea de actuación. NULL si no consta',
    tramo      TINYINT          NULL                       COMMENT '1, 2 o 3. Solo EELL 2025 según tamaño de municipio',
    PRIMARY KEY (id_conces),
    UNIQUE KEY uq_solic (id_solic),
    CONSTRAINT fk_conces_solic FOREIGN KEY (id_solic) REFERENCES solicitudes (id_solic)
);

-- ------------------------------------------------------------
-- AGRUPACIONES
-- Solo para EELL: concesiones presentadas como agrupación de ayuntamientos
-- ------------------------------------------------------------
CREATE TABLE agrupaciones (
    id_agrup       INT  NOT NULL AUTO_INCREMENT,
    id_conces      INT  NOT NULL,
    id_represent   INT  NOT NULL                           COMMENT 'Beneficiario que actúa como entidad representante',
    num_municipios INT  NULL                               COMMENT 'Número de municipios que forman la agrupación',
    PRIMARY KEY (id_agrup),
    UNIQUE KEY uq_conces (id_conces),
    CONSTRAINT fk_agrup_conces    FOREIGN KEY (id_conces)   REFERENCES concesiones   (id_conces),
    CONSTRAINT fk_agrup_represent FOREIGN KEY (id_represent) REFERENCES beneficiarios (id_benef)
);

-- ------------------------------------------------------------
-- AGRUPACION_MIEMBROS
-- Cada fila es un municipio miembro de una agrupación EELL
-- ------------------------------------------------------------
CREATE TABLE agrupacion_miembros (
    id_agrupM        INT           NOT NULL AUTO_INCREMENT,
    id_agrup         INT           NOT NULL,
    id_benef         INT           NOT NULL,
    importe_asignado DECIMAL(12,2) NULL                   COMMENT 'Importe asignado a este municipio dentro de la agrupación',
    PRIMARY KEY (id_agrupM),
    CONSTRAINT fk_miembro_agrup FOREIGN KEY (id_agrup) REFERENCES agrupaciones  (id_agrup),
    CONSTRAINT fk_miembro_benef FOREIGN KEY (id_benef) REFERENCES beneficiarios (id_benef)
);

-- ------------------------------------------------------------
-- CAUSAS_EXCLUSION  [FASE FUTURA]
-- Catálogo de causas por año y tipo (los códigos cambian cada año)
-- ------------------------------------------------------------
CREATE TABLE causas_exclusion (
    id_causa          INT         NOT NULL AUTO_INCREMENT,
    anio              INT         NOT NULL                 COMMENT 'Año de la convocatoria a la que aplica la causa',
    tipo_convoc       ENUM('epa','eell') NOT NULL,
    codigo_causa      VARCHAR(10) NOT NULL                 COMMENT 'Código oficial: 1, 6.a, A, 3.1...',
    descrip_exclusion TEXT        NOT NULL,
    articulo_conv     VARCHAR(20) NULL                     COMMENT 'Artículo de la convocatoria. Solo algunos años lo publican',
    PRIMARY KEY (id_causa),
    UNIQUE KEY uq_causa (anio, tipo_convoc, codigo_causa)
);

-- ------------------------------------------------------------
-- SOLICITUD_CAUSAS  [FASE FUTURA]
-- Tabla intermedia: una solicitud puede tener varias causas de exclusión
-- ------------------------------------------------------------
CREATE TABLE solicitud_causas (
    id_solic  INT NOT NULL,
    id_causa  INT NOT NULL,
    PRIMARY KEY (id_solic, id_causa),
    CONSTRAINT fk_sc_solic FOREIGN KEY (id_solic) REFERENCES solicitudes      (id_solic),
    CONSTRAINT fk_sc_causa FOREIGN KEY (id_causa) REFERENCES causas_exclusion (id_causa)
);
