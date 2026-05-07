# Tests — estrategia y resultados

El proyecto tiene dos niveles de pruebas:

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Tests automáticos | 123 | pytest (sin Docker) |
| Pruebas manuales | 31 | Navegador + DevTools con Docker levantado |
| **Total** | **154** | |

Las pruebas manuales se distribuyen en cuatro bloques: 6 de HTTPS/infraestructura, 13 de flujos del frontend, 10 de endpoints de la API vía `/docs` y 2 de caché y rate limiting.

---

## Tests automáticos (pytest)

El proyecto incluye **123 tests automáticos** distribuidos en 15 archivos que cubren la API REST, el sistema de autenticación, el pipeline de datos, los parsers, el sistema de logging, la configuración HTTPS, el endpoint de avisos, las cabeceras de caché y la configuración de rate limiting.

### Cómo funcionan

En vez de conectarse a la base de datos real (MariaDB en Docker), los tests de endpoints usan una base de datos **SQLite en memoria** que se crea antes de cada test y desaparece al terminar. Esto permite ejecutarlos en cualquier momento sin depender de Docker.

La configuración compartida está en `tests/conftest.py`:

- Crea un motor SQLite con `StaticPool` (todas las conexiones comparten la misma BD en memoria)
- Sustituye la dependencia `get_db` de FastAPI para que apunte a SQLite en vez de MariaDB
- Expone los fixtures `client` (cliente HTTP de prueba) y `db` (sesión de BD para insertar datos de prueba)

### Ejecutar los tests

```bash
source venv/bin/activate
pytest -v                          # todos los tests
pytest tests/test_auth.py -v      # solo un archivo
pytest -k "filtro"                 # solo tests cuyo nombre contiene "filtro"
```

### Tabla completa de tests

| # | Archivo | Tipo | Caja | Qué comprueba |
|---|---|---|---|---|
| 1 | `test_smoke.py` | Smoke | Negra | `GET /` responde 200 con `{"mensaje": "API funcionando"}` |
| 2 | `test_convocatorias.py` | Funcional | Negra | `GET /convocatorias/` responde 200 |
| 3 | `test_convocatorias.py` | Funcional | Negra | La respuesta es una lista JSON |
| 4 | `test_convocatorias.py` | Funcional | Negra | Con BD vacía devuelve `[]` sin error (robustez) |
| 5 | `test_solicitudes.py` | Funcional | Negra | `GET /solicitudes/` responde 200 |
| 6 | `test_solicitudes.py` | Funcional | Negra | La respuesta tiene las claves `total` y `resultados` |
| 7 | `test_solicitudes.py` | Funcional | Blanca | Filtro `?tipo=epa` devuelve solo solicitudes EPA; `total` correcto |
| 8 | `test_solicitudes.py` | Funcional | Blanca | Filtro `?estado=concedida` devuelve solo las concedidas; `total` correcto |
| 9 | `test_solicitudes.py` | Funcional | Blanca | Paginación: `total` no cambia entre páginas; registros por página correctos |
| 10 | `test_solicitudes.py` | Funcional | Blanca | Filtro `?cif=` devuelve solo solicitudes del beneficiario con ese CIF |
| 11 | `test_solicitudes.py` | Funcional | Blanca | `?buscar=Protectora` devuelve solo solicitudes cuya entidad contiene "Protectora" |
| 12 | `test_solicitudes.py` | Funcional | Blanca | Stopwords ignoradas: `buscar=Ayuntamiento de Burgos` equivale a `buscar=Burgos` |
| 13 | `test_solicitudes.py` | Funcional | Blanca | Búsqueda sin coincidencias devuelve `total: 0` y `resultados: []` sin error |
| 14 | `test_estadisticas.py` | Funcional | Negra | `GET /estadisticas/` responde 200 |
| 15 | `test_estadisticas.py` | Funcional | Negra | El JSON tiene las 4 claves esperadas |
| 16 | `test_estadisticas.py` | Funcional | Blanca | Totales calculados correctos con datos reales |
| 17 | `test_estadisticas.py` | Funcional | Blanca | Desglose por año y tipo correcto |
| 18 | `test_auth.py` | Funcional | Blanca | Registro válido devuelve 201 con email y rol |
| 19 | `test_auth.py` | Funcional | Blanca | Registro con email duplicado devuelve 400 |
| 20 | `test_auth.py` | Unitario | Blanca | Contraseña débil rechazada con 422 (validador Pydantic) |
| 21 | `test_auth.py` | Funcional | Blanca | Login correcto devuelve token JWT con `token_type: bearer` |
| 22 | `test_auth.py` | Funcional | Blanca | Login con contraseña incorrecta devuelve 401 |
| 23 | `test_auth.py` | Funcional | Blanca | Login con email inexistente devuelve 401 |
| 24 | `test_auth.py` | Seguridad | Blanca | `GET /privado/perfil` sin token devuelve 401 |
| 25 | `test_auth.py` | Seguridad | Blanca | `GET /privado/perfil` con token válido devuelve 200 |
| 26 | `test_auth.py` | Seguridad | Blanca | `GET /privado/resumen-exclusivo` sin token devuelve 401 |
| 27 | `test_auth.py` | Seguridad | Blanca | `GET /privado/resumen-exclusivo` con token válido devuelve 200 |
| 28–48 | `test_unificar_datasets.py` | Unitario | Blanca | Funciones de normalización de estados, limpieza de importes, entidades y puntuaciones |
| 49–70 | `test_parser_epa2025.py` | Unitario | Blanca | Helpers de detección (CIF, expediente, número europeo), mapeo de columnas, extracción de entidad con fallback, normalización de línea, flujo completo con XML mínimo mockeado |
| 71 | `test_smoke.py` | Smoke | Negra | `GET /health` responde 200 |
| 72 | `test_smoke.py` | Funcional | Negra | Respuesta de `/health` es exactamente `{"status": "ok"}` |
| 73 | `test_agrupaciones.py` | Funcional | Negra | ID inexistente en `/agrupaciones/` devuelve 404 |
| 74 | `test_agrupaciones.py` | Funcional | Blanca | Solicitud sin concesión ni agrupación devuelve 404 |
| 75 | `test_agrupaciones.py` | Funcional | Negra | Respuesta tiene las claves `id_agrup`, `num_municipios`, `representante`, `miembros` |
| 76 | `test_agrupaciones.py` | Funcional | Blanca | `num_municipios` coincide con el valor insertado en la fixture |
| 77 | `test_agrupaciones.py` | Funcional | Negra | Cada miembro tiene `nombre`, `cif` e `importe_asignado` |
| 78 | `test_solicitudes.py` | Funcional | Negra | `GET /solicitudes/export` devuelve `Content-Type: text/csv` |
| 79 | `test_solicitudes.py` | Funcional | Blanca | Primera línea del CSV tiene exactamente las 12 columnas esperadas |
| 80 | `test_solicitudes.py` | Funcional | Blanca | Con 3 solicitudes en BD, el CSV tiene cabecera + 3 filas de datos |
| 81 | `test_solicitudes.py` | Funcional | Blanca | `?tipo=epa` en export devuelve solo filas con tipo `epa` |
| 82 | `test_solicitudes.py` | Funcional | Negra | `Content-Disposition` incluye `attachment` y `solicitudes.csv` |
| 83 | `test_logging.py` | Funcional | Blanca | El middleware registra en el log el método y la ruta de cada request |
| 84 | `test_logging.py` | Funcional | Blanca | El código HTTP de la respuesta (ej. 404) aparece en el log |
| 85 | `test_logging.py` | Funcional | Blanca | La IP del cliente queda registrada en cada entrada del log |
| 86 | `test_logging.py` | Unitario | Blanca | `generic_exception_handler` llama a `logger.error` con el tipo de excepción |
| 87 | `test_logging.py` | Unitario | Blanca | `setup_logging()` devuelve un logger con nombre `bdns`, nivel INFO y al menos un handler |
| 88 | `test_avisos.py` | Funcional | Negra | `GET /avisos/` responde 200 y devuelve lista |
| 89 | `test_avisos.py` | Funcional | Negra | Con BD vacía devuelve `[]` sin error |
| 90 | `test_avisos.py` | Funcional | Blanca | Solo devuelve convocatorias del año actual con `fecha_resolucion = NULL` (filtra las resueltas y las de años anteriores) |
| 91 | `test_avisos.py` | Funcional | Blanca | La respuesta tiene las claves `id_convoc`, `titulo_convoc`, `tipo_convoc`, `anio_convocatoria`, `fecha_convocatoria` |
| 92 | `test_avisos.py` | Funcional | Blanca | Todos los avisos devueltos tienen `anio_convocatoria` igual al año en curso |
| 93 | `test_avisos.py` | Funcional | Blanca | Convocatorias con `fecha_resolucion` no nula no aparecen en la respuesta |
| 94 | `test_https_config.py` | Configuración | Blanca | El archivo `server.crt` existe en `docker/ssl/` |
| 95 | `test_https_config.py` | Seguridad | Blanca | `server.key` está excluida del repositorio vía `.gitignore` |
| 96 | `test_https_config.py` | Configuración | Blanca | El certificado tiene `CN=subvencionesDGDA.local` |
| 97 | `test_https_config.py` | Configuración | Blanca | El certificado incluye `subjectAltName` con el dominio (requerido por navegadores modernos) |
| 98 | `test_https_config.py` | Configuración | Blanca | El certificado no ha expirado |
| 99 | `test_https_config.py` | Configuración | Blanca | `default.conf` contiene `listen 443 ssl` |
| 100 | `test_https_config.py` | Configuración | Blanca | `default.conf` contiene `return 301 https://` (redirección HTTP→HTTPS) |
| 101 | `test_https_config.py` | Seguridad | Blanca | `default.conf` incluye la cabecera `Strict-Transport-Security` |
| 102 | `test_https_config.py` | Seguridad | Blanca | `default.conf` limita los protocolos a TLS 1.2 y TLS 1.3 |
| 103 | `test_cache_headers.py` | Rendimiento | Negra | `GET /convocatorias/` incluye `Cache-Control: public` en la respuesta |
| 104 | `test_cache_headers.py` | Rendimiento | Negra | `GET /convocatorias/` incluye `max-age=86400` (1 día) |
| 105 | `test_cache_headers.py` | Rendimiento | Negra | `GET /estadisticas/` incluye `Cache-Control: public` en la respuesta |
| 106 | `test_cache_headers.py` | Rendimiento | Negra | `GET /estadisticas/` incluye `max-age=3600` (1 hora) |
| 107 | `test_rate_limiting.py` | Configuración | Blanca | `default.conf` contiene `limit_req_zone` |
| 108 | `test_rate_limiting.py` | Configuración | Blanca | `default.conf` define la zona `login` para rate limiting |
| 109 | `test_rate_limiting.py` | Configuración | Blanca | `default.conf` establece el límite en `10r/m` (10 peticiones/minuto) |
| 110 | `test_rate_limiting.py` | Seguridad | Blanca | `default.conf` devuelve código `429` al superar el límite |
| 111 | `test_rate_limiting.py` | Seguridad | Blanca | El rate limiting se aplica al bloque `/auth/login` y no al resto de la API |
| 112 | `test_privado.py` | Seguridad | Blanca | `PUT /privado/cambiar-contrasena` sin token devuelve 401 |
| 113 | `test_privado.py` | Funcional | Blanca | Contraseña actual incorrecta devuelve 401 |
| 114 | `test_privado.py` | Funcional | Blanca | Nueva contraseña débil devuelve 422 (validador Pydantic) |
| 115 | `test_privado.py` | Funcional | Blanca | Cambio correcto devuelve 200 con campo `mensaje` |
| 116 | `test_privado.py` | Funcional | Blanca | Tras el cambio, el login con la contraseña nueva devuelve 200 |
| 117 | `test_privado.py` | Funcional | Blanca | Tras el cambio, el login con la contraseña vieja devuelve 401 |
| 118 | `test_refresh_token.py` | Funcional | Blanca | `POST /auth/login` devuelve `refresh_token` de 64 caracteres |
| 119 | `test_refresh_token.py` | Funcional | Blanca | `POST /auth/refresh` con token válido devuelve nuevo `access_token` |
| 120 | `test_refresh_token.py` | Seguridad | Blanca | El token usado en `/auth/refresh` queda revocado (rotación); el nuevo sí funciona |
| 121 | `test_refresh_token.py` | Seguridad | Blanca | Token inventado en `/auth/refresh` devuelve 401 |
| 122 | `test_refresh_token.py` | Seguridad | Blanca | `POST /auth/logout` revoca el token; un `/auth/refresh` posterior devuelve 401 |
| 123 | `test_refresh_token.py` | Funcional | Blanca | Logout con token inexistente devuelve 200 sin error |

### Descripción por módulo

#### test_smoke.py

Comprueba lo más básico: que la API arranca y responde. Si este test falla, algo fundamental está roto.

#### test_convocatorias.py

Verifica que `/convocatorias/` responde correctamente, que devuelve una lista JSON y que no da error cuando la base de datos está vacía (devuelve `[]`, no un fallo 500).

#### test_solicitudes.py

Inserta 3 solicitudes de prueba con dos beneficiarios distintos (EPA/asociación y EELL/entidad local) y comprueba filtros, paginación y búsqueda. Incluye el filtro `?cif=` (añadido en la fase 8b) y verifica que la respuesta tiene el formato `{"total": N, "resultados": [...]}` que permite al frontend mostrar "Página X de Y".

**Nota:** estos tests se actualizaron durante el desarrollo cuando se cambió el formato de respuesta de lista directa a objeto paginado. El test `test_solicitudes_devuelve_lista` se renombró a `test_solicitudes_estructura_paginada` y se adaptaron todos los que accedían a `response.json()` directamente como lista.

#### test_estadisticas.py

Verifica que el endpoint de estadísticas responde, que el JSON tiene la estructura esperada y que los cálculos de totales e importes son correctos con datos reales.

#### test_auth.py

Los tests más importantes. Cubren tres bloques:

- **Registro**: usuario nuevo se crea correctamente, email duplicado es rechazado (400), contraseña débil es rechazada por el validador Pydantic (422).
- **Login**: credenciales correctas devuelven token JWT; contraseña incorrecta o email inexistente devuelven 401.
- **Zona privada**: los endpoints `/privado/perfil` y `/privado/resumen-exclusivo` devuelven 401 sin token y 200 con token válido.

#### test_agrupaciones.py

Verifica el endpoint `/agrupaciones/{id_solic}`, que devuelve el desglose de municipios miembro de una agrupación EELL. Cubre los casos de error (ID inexistente, solicitud sin agrupación asociada) y el camino feliz con una fixture completa que construye toda la cadena de relaciones: Convocatoria → Beneficiario → Solicitud → Concesion → Agrupacion → AgrupacionMiembro.

**Bug detectado por estos tests:** el router usaba `joinedload("miembros")` y `joinedload("representante")` con strings, que no están admitidos en SQLAlchemy 2.x. Los tests fallaron con `ArgumentError` en todos los entornos, lo que llevó a corregir el router para usar atributos de clase (`Agrupacion.miembros`, `Agrupacion.representante`).

#### test_avisos.py

Verifica el endpoint `/avisos/` añadido en la rama `9e`. Cubre tres casos principales: BD vacía devuelve lista vacía, solo se devuelven convocatorias del año en curso sin resolución (las que tienen `fecha_resolucion IS NULL`), y las convocatorias ya resueltas o de años anteriores quedan excluidas. Incluye una fixture que inserta tres convocatorias con distintas combinaciones de año y estado de resolución para cubrir los casos límite.

#### test_privado.py

Verifica el endpoint `PUT /privado/cambiar-contrasena`. Cubre los tres casos de error (sin token → 401, contraseña actual incorrecta → 401, nueva contraseña débil → 422) y el camino feliz completo: el cambio devuelve 200, el login con la contraseña nueva funciona, y el login con la contraseña vieja falla. Este último par de tests es el más importante: confirma que el hash en base de datos se actualizó realmente.

#### test_refresh_token.py

Verifica el sistema de refresh token implementado en la rama `9gh`. Cubre el ciclo completo: el login genera un token opaco de 64 caracteres, el refresh devuelve un nuevo access token y rota el refresh token (el anterior queda revocado), un token inventado o ya usado devuelve 401, y el logout revoca correctamente el token en la base de datos. El test de rotación es el más importante: garantiza que cada refresh token solo puede usarse una vez, lo que limita el daño si un token es interceptado.

#### test_cache_headers.py

Verifica que los endpoints con datos raramente cambiantes incluyen la cabecera `Cache-Control` correcta. `/convocatorias/` recibe `public, max-age=86400` (1 día); `/estadisticas/` recibe `public, max-age=3600` (1 hora). La cabecera se inyecta en el router FastAPI mediante el parámetro `Response`, que FastAPI resuelve automáticamente como dependencia.

#### test_rate_limiting.py

Verifica la configuración de rate limiting en Nginx siguiendo el mismo patrón que `test_https_config.py`: lee `docker/nginx/default.conf` directamente sin necesitar Docker levantado. Comprueba que la zona `login` está definida con un límite de `10r/m`, que el status de rechazo es `429` y que el bloque de rate limiting está asociado únicamente a `/auth/login`.

#### test_logging.py

Verifica el sistema de logging implementado en la rama `9c`. Cubre dos partes:

- **Middleware de requests**: comprueba que cada petición HTTP queda registrada con método, ruta, código de respuesta e IP del cliente. Usa `caplog` de pytest para capturar los registros del logger `bdns` sin necesitar archivos en disco.
- **Configuración del logger**: verifica directamente la función `setup_logging()` y el `generic_exception_handler` usando mocks para no depender del sistema de archivos ni de llamadas HTTP reales.

#### test_unificar_datasets.py

Prueba las funciones puras de transformación de `unificar_datasets.py`. El caso más relevante: `normalizar_estado_epa` mapea "denegada" a valores distintos según el año (≤2023 → `excluida`; ≥2024 → `no_beneficiaria`), porque el BOE usa la misma palabra para dos realidades distintas.

#### test_parser_epa2025.py

Prueba las funciones del parser EPA 2025 con XMLs mínimos generados en memoria (sin conexión a internet). Documenta dos bugs históricos resueltos:

- `mapear_indices`: la columna "Concedido entidad – Euros" sobreescribía el índice de la columna Entidad. Ahora va a `importe_idx`.
- `extraer_entidad_2025`: cuando el índice apuntaba al importe en lugar del nombre, el fallback heurístico recupera el nombre real recorriendo las celdas.

### Tipos de test utilizados

- **Smoke**: verifica que el sistema arranca y responde mínimamente.
- **Funcional**: comprueba que una funcionalidad completa (endpoint + lógica + BD) produce el resultado esperado.
- **Unitario**: prueba una pieza de lógica aislada (validador de contraseña, funciones de normalización, helpers del parser).
- **Seguridad**: verifica que el control de acceso funciona correctamente (rutas protegidas).
- **Configuración**: verifica que los archivos de infraestructura (certificados, Nginx) tienen el contenido correcto sin necesitar el stack levantado.

La técnica de **caja negra** se aplica cuando el test solo mira la entrada y la salida (código de respuesta, estructura JSON). La técnica de **caja blanca** se aplica cuando el test conoce la lógica interna y diseña los casos en función de ella (filtros, paginación, validaciones específicas, casos límite del parser).

---

## Pruebas manuales de HTTPS

Realizadas con Docker levantado y `subvencionesDGDA.local` añadido al `/etc/hosts`.

| # | Prueba | Resultado esperado | Verificado |
|---|--------|-------------------|------------|
| 1 | `https://subvencionesDGDA.local` en el navegador | Carga la aplicación con aviso de certificado autofirmado; al aceptar, funciona completamente | ✔ |
| 2 | `http://subvencionesDGDA.local` en el navegador | Redirige automáticamente a HTTPS (código 301 visible en Network del DevTools) | ✔ |
| 3 | Network tab del DevTools en `/solicitudes/` | La petición fetch a la API va por `https://` y devuelve 200 | ✔ |
| 4 | Headers de respuesta en DevTools | `Strict-Transport-Security`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` presentes | ✔ |
| 5 | `Remote Address` en DevTools | Muestra `127.0.0.1:443` — confirma que va por el puerto HTTPS | ✔ |
| 6 | `http://localhost` sigue funcionando | La aplicación sigue accesible por localhost sin romper el flujo de desarrollo | ✔ |

---

## Pruebas manuales del frontend

Las pruebas manuales se realizaron navegando por la aplicación en `http://localhost/` con la aplicación levantada en Docker. Se verificaron los flujos principales y se detectaron tres errores que no estaban cubiertos por los tests automáticos.

### Flujos verificados

| # | Pantalla | Acción | Resultado esperado | OK |
|---|----------|--------|-------------------|-----|
| 1 | Inicio | Carga de métricas del dashboard | Números correctos (6398 solicitudes, 8 convocatorias, etc.) | ✔ |
| 2 | Solicitudes | Buscar sin filtros | Tabla con resultados y "Página 1 de N" | ✔ |
| 3 | Solicitudes | Filtrar por tipo EPA | Solo aparecen protectoras de animales | ✔ |
| 4 | Solicitudes | Filtrar por tipo EELL | Solo aparecen ayuntamientos; aparecen filtros CCAA y Provincia | ✔ |
| 5 | Solicitudes | Filtrar por EPA 2025 | Aparece el filtro de Línea de actuación | ✔ |
| 6 | Solicitudes | Navegar entre páginas | El contador "Página X de Y" se actualiza correctamente | ✔ |
| 7 | Solicitudes | Clic en una fila | Navega a la ficha de entidad con el CIF correcto | ✔ |
| 8 | Ficha entidad | Carga con `?cif=` en la URL | Muestra solo las solicitudes de esa entidad | ✔ |
| 9 | Login | Introducir contraseña incorrecta | Mensaje de error sin revelar si el email existe | ✔ |
| 10 | Login | Intentar acceder a zona privada sin sesión | Redirige al login | ✔ |
| 11 | Registro | Contraseña sin mayúscula | Validación client-side impide enviar el formulario | ✔ |
| 12 | Zona privada | Acceder con sesión activa | Muestra email, fecha de alta y rol correctamente | ✔ |
| 13 | Estadísticas | Carga de gráficos | Los tres gráficos se renderizan con datos reales | ✔ |

### Errores detectados y corregidos

#### Error 1 — Filtro CCAA no devolvía resultados en ninguna comunidad

**Detectado en:** prueba manual del filtro de CCAA en el buscador de solicitudes.

**Síntoma:** al seleccionar cualquier comunidad autónoma y buscar, el resultado era siempre "No se encontraron solicitudes". Afectaba a las 17 comunidades del selector.

**Causa:** los atributos `value` de las opciones del `<select>` usaban claves internas sin tildes ni espacios (ej: `"valencia"`, `"madrid"`, `"castilla_la_mancha"`), mientras que la base de datos almacena los nombres oficiales completos (ej: `"Comunidad Valenciana"`, `"Comunidad de Madrid"`, `"Castilla-La Mancha"`). El backend hace una comparación exacta, por lo que nunca coincidían.

**Corrección:** se actualizaron los 17 `value` del select en `solicitudes.html` para que coincidan exactamente con los valores de la BD. Algunos casos especiales:

| Valor anterior | Valor corregido |
|---|---|
| `valencia` | `Comunidad Valenciana` |
| `madrid` | `Comunidad de Madrid` |
| `asturias` | `Principado de Asturias` |
| `navarra` | `Comunidad Foral de Navarra` |
| `baleares` | `Illes Balears` |
| `murcia` | `Región de Murcia` |

Además se añadieron **Ceuta** (`Ciudad Autónoma de Ceuta`) y **Melilla** (`Ciudad Autónoma de Melilla`), que existían en la BD pero no aparecían en el selector.

---

#### Error 2 — El selector de año mostraba 2021 y 2022 al filtrar por EELL

**Detectado en:** prueba manual del filtro de tipo EELL.

**Síntoma:** al seleccionar "EELL (ayuntamientos)" en el filtro de tipo, el desplegable de año seguía mostrando todas las opciones (2021–2025), incluyendo 2021 y 2022, años en los que no existe ninguna convocatoria EELL. Seleccionar esos años devolvía 0 resultados sin ningún aviso.

**Causa:** la función `actualizarFiltrosCondicionales()` en `solicitudes.js` gestionaba la visibilidad de los filtros CCAA, Provincia y Línea, pero no contenía lógica para filtrar las opciones del selector de año según el tipo seleccionado.

**Corrección:** se añadió lógica a `actualizarFiltrosCondicionales()` para ocultar las opciones 2021 y 2022 cuando el tipo es EELL, y para resetear el año seleccionado si el valor actual deja de estar disponible al cambiar de tipo.

---

### Comportamiento verificado del buscador por nombre

Se comprobó que el campo de búsqueda por nombre de entidad es tolerante a variaciones de escritura gracias a la configuración de cotejamiento (collation) de MariaDB:

| Búsqueda introducida | Resultado |
|---|---|
| `PROTECTORA` | Igual que `protectora` (insensible a mayúsculas) |
| `asociacion` | Igual que `asociación` (insensible a tildes) |
| `A Coruna` | Igual que `A Coruña` (la ñ se trata como n) |

El filtro de provincia (campo de texto libre) tiene el mismo comportamiento: el usuario puede escribir `Malaga`, `málaga` o `MÁLAGA` y obtendrá los mismos resultados.

---

## Prueba manual rápida de la API (con Docker levantado)

Para verificar los endpoints directamente o preparar una demostración, abrir `http://localhost/docs`.

Crear el usuario de demo en `POST /auth/registro`:

```json
{
  "email": "demo@bdns.es",
  "password": "Demo1234"
}
```

Respuesta esperada: `201`. Después hacer login en `POST /auth/login` con las mismas credenciales, copiar el `access_token` y pegarlo en el botón **Authorize** (campo HTTPBearer).

### Casos probados

| # | Endpoint | Parámetros | Código | Resultado |
|---|----------|-----------|--------|-----------|
| 1 | `GET /solicitudes/` | `anio=aaaa` | 422 | Error de validación — FastAPI rechaza el tipo incorrecto |
| 2 | `GET /solicitudes/` | `anio=2025&tipo=epa&limite=5&pagina=2` | 200 | Segunda página de EPA 2025, 5 registros, `total` correcto |
| 3 | `GET /solicitudes/` | `anio=2024&tipo=epa&estado=no_beneficiaria&limite=2` | 200 | 2 primeras EPA 2024 no beneficiarias |
| 4 | `GET /solicitudes/` | `tipo=eell&estado=concedida&limite=8` | 200 | 8 EELL concedidas |
| 5 | `GET /solicitudes/` | `cif=G23705205` | 200 | Solo solicitudes de ese CIF; `total` = número real de sus solicitudes |
| 6 | `GET /convocatorias/` | — | 200 | Lista de las 8 convocatorias del sistema |
| 7 | `GET /estadisticas/` | — | 200 | Agregados por año y tipo con importes totales |
| 8 | `GET /privado/perfil` | sin token | 401 | `{"error": 401, "mensaje": "No autenticado", ...}` |
| 9 | `GET /privado/perfil` | con token | 200 | Email, rol y fecha de alta del usuario |
| 10 | `GET /privado/resumen-exclusivo` | con token | 200 | Mensaje de bienvenida y lista de contenido exclusivo |

---

## Pruebas manuales de caché y rate limiting

Realizadas con Docker levantado. Verifican el comportamiento en el stack completo (Nginx → FastAPI) que los tests automáticos no pueden cubrir directamente.

| # | Prueba | Cómo realizarla | Resultado esperado | Verificado |
|---|--------|-----------------|-------------------|------------|
| 1 | `Cache-Control` en `/convocatorias/` | Abrir `https://subvencionesDGDA.local/convocatorias/` en el navegador con F12 → Network → seleccionar la petición → Response Headers | `cache-control: public, max-age=86400` visible en las cabeceras de respuesta | ✔ |
| 2 | Rate limiting en `/auth/login` | Ejecutar el bucle curl de abajo desde la terminal WSL | Los primeros 6 intentos (1 base + 5 burst) devuelven `401`; a partir del 7.º devuelven `429 Too Many Requests` | ✔ |

### Comando para verificar el rate limiting

```bash
for i in $(seq 1 16); do
  curl -sk -o /dev/null -w "%{http_code}\n" \
    -X POST https://subvencionesDGDA.local/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"x@x.com","password":"Mal1234"}';
done
```

Resultado esperado:

```text
401  ← peticiones 1-6 (dentro del límite + burst)
401
401
401
401
401
429  ← peticiones 7-16 (límite superado)
429
429
...
```
