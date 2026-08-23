-- ============================================================
-- Modelo físico: Análisis de subvenciones DGDA
-- Base de datos: bdns_dgda
-- Tablas implementadas: convocatorias, beneficiarios, solicitudes,
--   concesiones, agrupaciones, agrupacion_miembros, usuarios, refresh_tokens,
--   reset_tokens
-- Tablas fase futura: solicitud_causas
-- ============================================================
-- Notas:
--   - Se usa CREATE TABLE IF NOT EXISTS para evitar errores si el
--     script se ejecuta sobre una BD ya inicializada.
--   - No se incluyen DROP TABLE: el reset se hace a nivel de volumen
--     Docker (docker-compose down -v) para evitar pérdidas accidentales.
--   - causas_exclusion SÍ se crea (más abajo): es el catálogo que traduce
--     el código de exclusión al motivo redactado, y se carga desde
--     data/final/causas_exclusion.json. La cabecera la daba por futura
--     desde el diseño inicial, cuando aún no existía.
--   - solicitud_causas sigue siendo futura: hoy los códigos van en el
--     campo causa_exclusion de solicitudes, separados por ';', en vez de
--     en una tabla de relación.
-- ============================================================

CREATE DATABASE IF NOT EXISTS bdns_dgda
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE bdns_dgda;

-- ------------------------------------------------------------
-- CONVOCATORIAS
-- Una fila por convocatoria anual (EPA y EELL son separadas)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS convocatorias (
    id_convoc          INT          NOT NULL AUTO_INCREMENT,
    num_convoc         VARCHAR(50)  NULL                    COMMENT 'Número oficial de convocatoria BDNS',
    titulo_convoc      VARCHAR(255) NOT NULL                COMMENT 'Descripción/título de la convocatoria',
    tipo_convoc        ENUM('epa','eell') NOT NULL          COMMENT 'epa = protectoras, eell = entidades locales',
    anio_convocatoria  INT          NOT NULL                COMMENT 'Año de la convocatoria (2021-2025)',
    fecha_convocatoria DATE         NULL                    COMMENT 'Fecha de publicación de la convocatoria',
    fecha_fin_plazo    DATE         NULL                    COMMENT 'Fecha de fin del plazo de solicitud (NULL hasta que se conoce)',
    fecha_resolucion   DATE         NULL                    COMMENT 'Fecha de resolución definitiva',
    periodo_meses      TINYINT      NOT NULL DEFAULT 12     COMMENT 'Duración del periodo subvencionable en meses. EPA 2023/2024 y EELL 2023 = 6; resto = 12',
    periodo_anio       VARCHAR(16)  NULL                    COMMENT 'Año o años de gasto que financia la convocatoria. NO coincide con anio_convocatoria: las EPA de 2021-2024 y las EELL financian el año siguiente. NULL si el extracto del BOE no lo declara',
    periodo_matiz      VARCHAR(40)  NULL                    COMMENT 'Precisión sobre el periodo cuando no es el año completo, p. ej. «1.er semestre». NULL si cubre el año entero',
    PRIMARY KEY (id_convoc)
);

-- ------------------------------------------------------------
-- BENEFICIARIOS
-- Entidades que presentan solicitudes (asociaciones o ayuntamientos)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS beneficiarios (
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
CREATE TABLE IF NOT EXISTS solicitudes (
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
    provincia      VARCHAR(100)     NULL                   COMMENT 'Provincia derivada del CIF. Solo disponible para EELL; NULL para EPA',
    ccaa           VARCHAR(100)     NULL                   COMMENT 'Comunidad autónoma derivada del CIF. Solo disponible para EELL; NULL para EPA',
    causa_exclusion VARCHAR(100)    NULL                   COMMENT 'Código(s) de causa de exclusión separados por ";" (leyenda en causas_exclusion). Solo estado=excluida',
    PRIMARY KEY (id_solic),
    -- Clave compuesta: el mismo num_expediente puede aparecer en convocatorias distintas
    -- (entidades que desistieron un año y volvieron al siguiente).
    UNIQUE KEY uq_expediente (num_expediente, id_convoc),
    INDEX idx_solic_estado    (estado),
    INDEX idx_solic_provincia (provincia),
    INDEX idx_solic_ccaa      (ccaa),
    CONSTRAINT fk_solic_convoc FOREIGN KEY (id_convoc) REFERENCES convocatorias (id_convoc),
    CONSTRAINT fk_solic_benef  FOREIGN KEY (id_benef)  REFERENCES beneficiarios  (id_benef)
);

-- ------------------------------------------------------------
-- CAUSAS DE EXCLUSIÓN (catálogo)
-- Leyenda código -> motivo por (tipo, año). Cada convocatoria usa su propia
-- numeración, así que el código solo tiene sentido junto a tipo y año.
-- Se carga desde data/final/causas_exclusion.json en cargar_dataset.py
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS causas_exclusion (
    id_causa    INT              NOT NULL AUTO_INCREMENT,
    tipo_convoc ENUM('epa','eell') NOT NULL,
    anio        INT              NOT NULL,
    codigo      VARCHAR(10)      NOT NULL                  COMMENT 'Código tal como aparece en la resolución (1, 6.a, 3.1, B...)',
    motivo      VARCHAR(500)     NOT NULL                  COMMENT 'Texto del motivo de exclusión',
    articulo    VARCHAR(20)      NULL                      COMMENT 'Artículo de la convocatoria, si la leyenda lo indica',
    PRIMARY KEY (id_causa),
    UNIQUE KEY uq_causa (tipo_convoc, anio, codigo)
);

-- ------------------------------------------------------------
-- CONCESIONES
-- Solo existen cuando estado = 'concedida' e importe > 0
-- Las no_beneficiaria, excluidas y desistidas NO generan fila aquí
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS concesiones (
    id_conces  INT              NOT NULL AUTO_INCREMENT,
    id_solic   INT              NOT NULL,
    importe    DECIMAL(12,2)    NOT NULL DEFAULT 0.00      COMMENT 'Importe concedido en euros',
    linea      ENUM(
                 'animales_abandonados',
                 'colonias_felinas'
               ) NULL                                      COMMENT 'Línea EPA. Solo desde resolución 2025. NULL en años anteriores y en EELL (que ya tienen tipo_convoc=eell)',
    tramo      TINYINT          NULL                       COMMENT '1, 2 o 3. Solo EELL 2025 según tamaño de municipio',
    PRIMARY KEY (id_conces),
    UNIQUE KEY uq_solic (id_solic),
    CONSTRAINT fk_conces_solic FOREIGN KEY (id_solic) REFERENCES solicitudes (id_solic)
);

-- ------------------------------------------------------------
-- AGRUPACIONES
-- Solo para EELL: concesiones presentadas como agrupación de ayuntamientos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agrupaciones (
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
CREATE TABLE IF NOT EXISTS agrupacion_miembros (
    id_agrupM        INT           NOT NULL AUTO_INCREMENT,
    id_agrup         INT           NOT NULL,
    id_benef         INT           NOT NULL,
    importe_asignado DECIMAL(12,2) NULL                   COMMENT 'Importe asignado a este municipio dentro de la agrupación',
    PRIMARY KEY (id_agrupM),
    CONSTRAINT fk_miembro_agrup FOREIGN KEY (id_agrup) REFERENCES agrupaciones  (id_agrup),
    CONSTRAINT fk_miembro_benef FOREIGN KEY (id_benef) REFERENCES beneficiarios (id_benef)
);

-- ------------------------------------------------------------
-- USUARIOS
-- Gestión de acceso a la plataforma web.
-- Tres roles: admin (gestión), registrado (contenido exclusivo),
-- el acceso público no requiere usuario en BD.
-- Contraseñas siempre hasheadas (bcrypt), nunca en texto plano.
-- Autenticación mediante JWT (implementación fase siguiente).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario       INT          NOT NULL AUTO_INCREMENT,
    email            VARCHAR(255) NOT NULL,
    nombre           VARCHAR(100) NULL                          COMMENT 'Nombre o alias opcional del usuario',
    password         VARCHAR(255) NOT NULL                      COMMENT 'Hash bcrypt de la contraseña',
    rol              ENUM('admin','registrado') NOT NULL DEFAULT 'registrado',
    activo           TINYINT(1)   NOT NULL DEFAULT 1            COMMENT '0 = cuenta desactivada por admin',
    email_verificado TINYINT(1)   NOT NULL DEFAULT 0            COMMENT '0 = pendiente de verificar; 1 = email confirmado',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_email (email)
);

-- ------------------------------------------------------------
-- REFRESH TOKENS
-- Tokens de larga duración (30 días) para renovar el access token
-- sin que el usuario tenga que volver a hacer login.
-- Se emite uno por cada login. La rotación garantiza que cada token
-- solo puede usarse una vez; al renovar, el antiguo queda revocado.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INT          NOT NULL AUTO_INCREMENT,
    id_usuario  INT          NOT NULL,
    token       VARCHAR(64)  NOT NULL                      COMMENT 'Token opaco generado con secrets.token_hex(32)',
    expira_en   DATETIME     NOT NULL,
    revocado    TINYINT(1)   NOT NULL DEFAULT 0            COMMENT '1 = usado o cerrado por logout',
    PRIMARY KEY (id),
    UNIQUE KEY uq_token (token),
    CONSTRAINT fk_rt_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- RESET TOKENS
-- Tokens de un solo uso (15 min) para recuperar la contraseña.
-- Se genera uno por solicitud de recuperación. Una vez usado
-- o caducado, ya no es válido.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reset_tokens (
    id          INT          NOT NULL AUTO_INCREMENT,
    id_usuario  INT          NOT NULL,
    token       VARCHAR(64)  NOT NULL                      COMMENT 'Token opaco generado con secrets.token_hex(32)',
    expira_en   DATETIME     NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0            COMMENT '1 = ya utilizado',
    PRIMARY KEY (id),
    UNIQUE KEY uq_reset_token (token),
    CONSTRAINT fk_reset_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- VERIFICACIÓN DE EMAIL
-- Tokens de un solo uso (24 h) para confirmar la dirección de
-- email al registrarse. Hasta que no se usa el enlace,
-- email_verificado=0 en usuarios y el login queda bloqueado.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verificacion_tokens (
    id          INT          NOT NULL AUTO_INCREMENT,
    id_usuario  INT          NOT NULL,
    token       VARCHAR(64)  NOT NULL                      COMMENT 'Token opaco generado con secrets.token_hex(32)',
    expira_en   DATETIME     NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0            COMMENT '1 = ya utilizado',
    PRIMARY KEY (id),
    UNIQUE KEY uq_verif_token (token),
    CONSTRAINT fk_verif_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- SIN USUARIOS SEMBRADOS
-- Aquí había una cuenta de administración con su hash escrito.
-- Se retiró a propósito: este fichero está en el repositorio, así que
-- cualquiera que lo leyese conocería la contraseña de administración de
-- todo despliegue nuevo, y bastaría con ir al dominio y entrar.
--
-- La cuenta se crea al instalar, pidiendo la contraseña:
--   scripts/crear_admin.sh   (lo invocan install.sh y `make crear-admin`)
--
-- `make reset-db` lo llama al terminar, para no dejar la instalación sin
-- ninguna cuenta con la que entrar.
-- ------------------------------------------------------------
