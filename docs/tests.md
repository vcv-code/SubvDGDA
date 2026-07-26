# Tests — estrategia y resultados

El proyecto tiene dos niveles de pruebas:

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Tests automáticos | 246 funciones / 344 ejecuciones | pytest (sin Docker) |
| Pruebas manuales | 52 | Navegador + DevTools con Docker levantado |
| **Total** | **298 funciones / 396 ejecuciones** | |

Las pruebas manuales se distribuyen en seis bloques: 6 de HTTPS/infraestructura, 13 de flujos del frontend, 10 de endpoints de la API vía `/docs`, 2 de caché y rate limiting, 14 de las funcionalidades nuevas de rama 10 (agrupaciones, tramos, URL persistence y bloque convocatorias en Home) y 6 de recuperación de contraseña (rama 11b).

Nota sobre ejecución: 16 de las 344 ejecuciones automáticas requieren Docker y Nginx levantados (`test_https_config.py` y `test_rate_limiting.py`). Sin Docker, pasan 328. Con Docker completo, pasan las 344.

---

## Sobre el conteo de tests

A partir del archivo `test_scheduler.py` (verificación del calendario del cron) el proyecto incluye tests parametrizados. Pytest cuenta cada caso parametrizado como una ejecución independiente, por lo que el número de **ejecuciones** (344) es mayor que el número de **funciones de test** escritas (246). Ejemplo:

```python
@pytest.mark.parametrize("day", [1, 5, 9, 13, 17, 21, 25, 29])
def test_check_bdns_corre_en_marzo_cada_4_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 3, day, 8, 0))
```

Esa es **una función**, pero pytest la ejecuta 8 veces (una por cada día) y reporta 8 PASSED. `@pytest.mark.parametrize` es una técnica estándar de pytest para evitar duplicar código de test cuando solo cambian los datos de entrada.

Solo `test_scheduler.py` usa `parametrize`. Los otros 22 archivos tienen una correspondencia 1:1 entre funciones de test y ejecuciones.

---

## Qué no se testea y por qué

### `cargar_dataset.py`

No tiene tests por dos razones:

1. **Es lógica de inserción, no de transformación.** Su única responsabilidad es hacer INSERTs e IGNOREs correctamente. Los datos que inserta ya han sido validados por los tests del parser y del unificador.
2. **Requeriría una MariaDB real.** A diferencia del backend (que usa SQLite en memoria como sustituto), `cargar_dataset` usa características específicas de MariaDB (`ON DUPLICATE KEY`, tipos `ENUM`, `DECIMAL`) que SQLite no reproduce fielmente.

### Parsers de años anteriores y EELL

Los parsers EPA 2021–2024 y EELL (PDF y BOE) no tienen tests unitarios. Sus funciones de extracción son más simples o dependen de `pdfplumber` (difícil de mockear). La validación de sus datos se hace comparando los totales con los publicados en el BOE.

---

## SQLite vs MariaDB: diferencias conocidas

Los tests de endpoints usan SQLite en memoria como sustituto de MariaDB. Funciona bien para probar lógica de aplicación, pero no replica el comportamiento de MariaDB en tres puntos:

| Característica | MariaDB (producción) | SQLite (tests) |
|---|---|---|
| `ENUM` en columnas | Rechaza valores fuera del enum a nivel de BD | Lo acepta como texto cualquiera |
| `DECIMAL(12,2)` | Precisión fija, redondea al guardar | Se trata como float de Python |
| `ON DUPLICATE KEY UPDATE` | Sintaxis nativa para upserts | No existe |

Los tests actuales prueban **lógica de la aplicación** (filtros, respuestas HTTP, autenticación), no **integridad de la BD**, por lo que SQLite es suficiente. Si en el futuro se quisiera testear algo que dependa de estas diferencias, habría que añadir un contenedor MariaDB al entorno de CI con `@pytest.mark.integration`.

---

## Tests automáticos (pytest)

El proyecto incluye **246 funciones de test automáticas** (344 ejecuciones con pytest) distribuidas en 22 archivos que cubren la API REST, el sistema de autenticación, el panel de administración, la verificación de email, los refresh tokens, el formulario de contacto, el modo mantenimiento, el estado del plazo de las convocatorias, el pipeline de datos, los parsers, el sistema de logging, la configuración HTTPS, el endpoint de avisos, las cabeceras de caché, la configuración de rate limiting, el scheduler del cron y el helper de reintentos a la API BDNS.

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

> **Pendiente de actualizar:** esta tabla numerada es una foto que se quedó en 199 filas; la suite real ya tiene **378 funciones**. Falta regenerarla (y añadir, entre otros, los tests de tramos de importe y recurrencia EELL). Al hacerlo conviene automatizar la extracción desde `pytest --collect-only` para no volver a desincronizarla.

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
| 79 | `test_solicitudes.py` | Funcional | Blanca | Primera línea del CSV tiene exactamente las 13 columnas esperadas (incluye `tramo`) |
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
| 124 | `test_refresh_token.py` | Seguridad | Blanca | Cambiar contraseña revoca todos los refresh tokens activos del usuario |
| 125 | `test_estadisticas.py` | Funcional | Negra | `GET /estadisticas/epas` responde 200 |
| 126 | `test_estadisticas.py` | Funcional | Negra | Respuesta de `/estadisticas/epas` tiene las claves esperadas |
| 127 | `test_estadisticas.py` | Funcional | Blanca | Sin datos en BD, `/estadisticas/epas` devuelve ceros sin error |
| 128 | `test_estadisticas.py` | Funcional | Blanca | Cálculos globales de EPAs (importe medio, mediana, total) correctos con fixture |
| 129 | `test_estadisticas.py` | Funcional | Blanca | Entidades únicas (sin duplicados por año) calculadas correctamente |
| 130 | `test_estadisticas.py` | Funcional | Blanca | Nuevos vs recurrentes por año: la primera aparición cuenta como nuevo |
| 131 | `test_estadisticas.py` | Funcional | Blanca | Top beneficiarios devuelve el importe acumulado por entidad |
| 132 | `test_estadisticas.py` | Funcional | Blanca | Distribución por tramos: todos los rangos presentes en la respuesta |
| 133 | `test_estadisticas.py` | Rendimiento | Negra | `/estadisticas/epas` incluye cabecera `Cache-Control` |
| 134 | `test_estadisticas.py` | Funcional | Negra | `GET /estadisticas/eell` responde 200 |
| 135 | `test_estadisticas.py` | Funcional | Negra | Respuesta de `/estadisticas/eell` tiene las claves esperadas |
| 136 | `test_estadisticas.py` | Funcional | Blanca | Sin datos en BD, `/estadisticas/eell` devuelve ceros sin error |
| 137 | `test_estadisticas.py` | Funcional | Blanca | Porcentaje de ayuntamientos con ayuda calculado correctamente |
| 138 | `test_estadisticas.py` | Funcional | Blanca | Importe medio por entidad local correcto con fixture |
| 139 | `test_estadisticas.py` | Funcional | Blanca | Ratio de exclusión (excluidas / total evaluadas) correcto |
| 140 | `test_estadisticas.py` | Funcional | Blanca | CCAA top devuelve la comunidad con más concedidas |
| 141 | `test_estadisticas.py` | Funcional | Blanca | Desglose por CCAA tiene el recuento correcto por comunidad |
| 142 | `test_estadisticas.py` | Funcional | Blanca | Top provincias devuelve las provincias con más concedidas |
| 143 | `test_estadisticas.py` | Funcional | Blanca | Concentración top 10 %: los porcentajes suman exactamente 100 |
| 144 | `test_estadisticas.py` | Rendimiento | Negra | `/estadisticas/eell` incluye cabecera `Cache-Control` |
| 145 | `test_agrupaciones.py` | Funcional | Blanca | `representante` es un objeto con campo `nombre` (no `[object Object]`) |
| 146 | `test_agrupaciones.py` | Funcional | Blanca | `importe_asignado` de cada miembro coincide con el valor insertado en la fixture |
| 147 | `test_solicitudes.py` | Funcional | Blanca | Campo `tramo` aparece en la respuesta con el valor correcto para EELL 2025 concedidas |
| 148 | `test_solicitudes.py` | Funcional | Blanca | Campo `tramo` es `null` para solicitudes sin concesión |
| 149 | `test_recuperar_password.py` | Funcional | Negra | `POST /auth/recuperar` con email existente devuelve 200 |
| 150 | `test_recuperar_password.py` | Seguridad | Negra | `POST /auth/recuperar` con email inexistente devuelve también 200 (no revela si existe) |
| 151 | `test_recuperar_password.py` | Funcional | Blanca | Llamar a `/recuperar` crea exactamente un `ResetToken` en la BD |
| 152 | `test_recuperar_password.py` | Funcional | Blanca | La función `enviar_email_recuperacion` se llama con el email y el token correctos |
| 153 | `test_recuperar_password.py` | Funcional | Blanca | `POST /auth/reset` con token válido cambia la contraseña y el login posterior funciona |
| 154 | `test_recuperar_password.py` | Seguridad | Negra | `POST /auth/reset` con token inventado devuelve 400 |
| 155 | `test_recuperar_password.py` | Seguridad | Blanca | `POST /auth/reset` con token ya usado devuelve 400 (no se puede usar dos veces) |
| 156 | `test_recuperar_password.py` | Seguridad | Blanca | `POST /auth/reset` con token expirado (insertado con fecha en el pasado) devuelve 400 |
| 157 | `test_recuperar_password.py` | Unitario | Blanca | Contraseña nueva débil en `/auth/reset` devuelve 422 (validación Pydantic antes de comprobar el token) |
| 158 | `test_verificacion_email.py` | Funcional | Blanca | `POST /auth/registro` crea el usuario con `email_verificado=0` |
| 159 | `test_verificacion_email.py` | Funcional | Blanca | El registro inserta un token de verificación en `verificacion_tokens` |
| 160 | `test_verificacion_email.py` | Funcional | Blanca | La función de envío de email se llama con el email y token correctos |
| 161 | `test_verificacion_email.py` | Seguridad | Blanca | `POST /auth/login` devuelve 403 si el email no está verificado |
| 162 | `test_verificacion_email.py` | Funcional | Blanca | `GET /auth/verificar?token=...` válido establece `email_verificado=1` |
| 163 | `test_verificacion_email.py` | Funcional | Blanca | Login correcto tras verificar el email |
| 164 | `test_verificacion_email.py` | Seguridad | Negra | Token inventado en `/auth/verificar` devuelve 400 |
| 165 | `test_verificacion_email.py` | Seguridad | Blanca | Token ya usado en `/auth/verificar` devuelve 400 |
| 166 | `test_verificacion_email.py` | Seguridad | Blanca | Token expirado en `/auth/verificar` devuelve 400 |
| 167 | `test_verificacion_email.py` | Funcional | Blanca | `POST /auth/reset` exitoso también activa `email_verificado` |
| 168 | `test_admin.py` | Seguridad | Negra | `GET /admin/estado` sin token devuelve 401 |
| 169 | `test_admin.py` | Seguridad | Blanca | `GET /admin/estado` con rol `registrado` devuelve 403 |
| 170 | `test_admin.py` | Funcional | Blanca | `GET /admin/estado` con rol `admin` devuelve 200 con campos `total_solicitudes`, `total_usuarios`, `total_convocatorias` |
| 171 | `test_admin.py` | Funcional | Blanca | `GET /admin/usuarios` devuelve lista con email, rol, activo y created_at |
| 172 | `test_admin.py` | Funcional | Blanca | `PATCH /admin/usuarios/{id}/rol` cambia rol a `admin` |
| 173 | `test_admin.py` | Seguridad | Blanca | `PATCH /admin/usuarios/{id}/rol` sobre la propia cuenta devuelve 400 |
| 174 | `test_admin.py` | Funcional | Blanca | `PATCH /admin/usuarios/{id}/activo` desactiva la cuenta |
| 175 | `test_admin.py` | Seguridad | Blanca | `PATCH /admin/usuarios/{id}/activo` sobre la propia cuenta devuelve 400 |
| 176 | `test_admin.py` | Seguridad | Blanca | `PATCH /admin/usuarios/{id_inexistente}/activo` devuelve 404 |
| 177 | `test_admin.py` | Funcional | Blanca | `DELETE /admin/usuarios/{id}` elimina el usuario de la BD |
| 178 | `test_admin.py` | Seguridad | Blanca | `DELETE /admin/usuarios/{id}` sobre la propia cuenta devuelve 400 |
| 179 | `test_admin.py` | Seguridad | Blanca | `DELETE /admin/usuarios/{id_inexistente}` devuelve 404 |
| 180 | `test_admin.py` | Funcional | Blanca | `GET /admin/avisos` sin resolución devuelve solo avisos activos |
| 181 | `test_admin.py` | Funcional | Blanca | `GET /admin/avisos` con fecha_resolucion != NULL no aparece en la lista por defecto |
| 182 | `test_admin.py` | Funcional | Blanca | `PATCH /admin/avisos/{id}/desactivar` actualiza fecha_resolucion |
| 183 | `test_admin.py` | Funcional | Blanca | `DELETE /admin/avisos/{id}` sin solicitudes elimina la convocatoria |
| 184 | `test_admin.py` | Seguridad | Blanca | `DELETE /admin/avisos/{id}` con solicitudes asociadas devuelve 409 |
| 185 | `test_admin.py` | Funcional | Blanca | `PATCH /admin/avisos/{id}/reactivar` elimina fecha_resolucion |
| 186 | `test_admin.py` | Seguridad | Blanca | Reactivar aviso ya activo devuelve 400 |
| 187 | `test_admin.py` | Funcional | Blanca | `GET /admin/avisos?incluir_resueltas=true` devuelve avisos activos e inactivos |
| 188 | `test_admin.py` | Seguridad | Blanca | Aviso inexistente devuelve 404 |
| 189 | `test_admin.py` | Funcional | Blanca | `GET /admin/logs` devuelve una lista (aunque esté vacía) |
| 190 | `test_admin.py` | Funcional | Blanca | `GET /admin/logs/errores` devuelve una lista (aunque esté vacía) |
| 191 | `test_admin.py` | Seguridad | Blanca | `GET /admin/logs/errores` con rol `registrado` devuelve 403 |
| 192 | `test_scheduler.py` | Unitario | Blanca | `health_check.py` se ejecuta a las 00:00, 06:00, 12:00 y 18:00 UTC |
| 193 | `test_scheduler.py` | Unitario | Blanca | `health_check.py` no se ejecuta a horas fuera del calendario cada-6h |
| 194 | `test_scheduler.py` | Unitario | Blanca | `health_check.py` solo se ejecuta en el minuto 0 (no a las 06:30) |
| 195 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en marzo los días 1, 5, 9, 13, 17, 21, 25, 29 a las 08:00 UTC |
| 196 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` no corre en marzo los días intermedios (2, 3, 4, 6, 7, 8) |
| 197 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en abril cada 2 días (días 1, 3, 5, 7, …, 29) |
| 198 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en mayo cada 2 días (días 1, 3, 5, …, 31) |
| 199 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` no corre en mayo los días pares (2, 4, 6, …) |
| 200 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en junio cada 4 días (días 1, 5, 9, …, 29) |
| 201 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en noviembre cada 2 días (días 1, 3, 5, …, 29) |
| 202 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` no corre en noviembre los días pares (2, 4, 6, …) |
| 203 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en diciembre cada 2 días (días 1, 3, 5, …, 31) |
| 204 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` corre en enero cada 4 días (días 1, 5, 9, …, 29) |
| 205 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` no corre en enero los días intermedios (2, 3, 4, 6, 7, 8) |
| 206 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` no se ejecuta fuera de temporada (febrero, julio–octubre) ningún día del mes |
| 207 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` solo se ejecuta a las 08:00 UTC, no a otras horas aunque el día sea válido |
| 208 | `test_scheduler.py` | Unitario | Blanca | `check_bdns.py` solo se ejecuta en el minuto 0 (no a las 08:30) |
| 209 | `test_scheduler.py` | Unitario | Blanca | A medianoche en un día válido para `check_bdns` solo se ejecuta `health_check.py` |
| 210 | `test_scheduler.py` | Unitario | Blanca | A las 08:00 en un día válido para `check_bdns` solo se ejecuta `check_bdns.py` (no `health_check`) |
| 211 | `test_scheduler.py` | Unitario | Blanca | A las 08:00 en un día NO válido para `check_bdns` no se ejecuta ningún job |
| 212 | `test_scheduler.py` | Unitario | Blanca | En julio el `check_bdns.py` no se ejecuta nunca; el `health_check.py` sí continúa cada 6h |
| 213 | `test_check_bdns.py` | Unitario | Blanca | `_get_bdns_con_retry` devuelve la response al primer intento si BDNS responde 200 (sin sleeps) |
| 214 | `test_check_bdns.py` | Unitario | Blanca | Si BDNS falla en el 1.er intento y responde 200 en el 2.º, la función reintenta con sleep de 2s y devuelve la response |
| 215 | `test_check_bdns.py` | Unitario | Blanca | Si los 3 intentos fallan por error de red, la función devuelve None y hace 2 sleeps (entre intentos) |
| 216 | `test_check_bdns.py` | Unitario | Blanca | Si BDNS responde 500 las 3 veces, la función devuelve None tras 3 intentos |
| 217 | `test_check_bdns.py` | Unitario | Blanca | Los tiempos de espera entre reintentos siguen el patrón exponencial 2s → 4s (no constante ni lineal) |

### Descripción por módulo

#### test_smoke.py

Comprueba lo más básico: que la API arranca y responde. Si este test falla, algo fundamental está roto.

#### test_convocatorias.py

Verifica que `/convocatorias/` responde correctamente, que devuelve una lista JSON y que no da error cuando la base de datos está vacía (devuelve `[]`, no un fallo 500).

#### test_solicitudes.py

Inserta 3 solicitudes de prueba con dos beneficiarios distintos (EPA/asociación y EELL/entidad local) y comprueba filtros, paginación y búsqueda. Incluye el filtro `?cif=` (añadido en la fase 8b) y verifica que la respuesta tiene el formato `{"total": N, "resultados": [...]}` que permite al frontend mostrar "Página X de Y".

Incluye además el bloque de **causas de exclusión** (fixture `db_con_causas`): causa en la respuesta, filtro `?causa=` con match por token exacto ("6" no casa con "16" ni con "6.a"), códigos con punto (`6.a`), estructura del catálogo `GET /solicitudes/causas`, su Cache-Control de 24 h y la columna `causa_exclusion` en el CSV de exportación.

**Nota:** estos tests se actualizaron durante el desarrollo cuando se cambió el formato de respuesta de lista directa a objeto paginado. El test `test_solicitudes_devuelve_lista` se renombró a `test_solicitudes_estructura_paginada` y se adaptaron todos los que accedían a `response.json()` directamente como lista.

#### test_estadisticas.py

Cubre tres endpoints: el general `/estadisticas/` (4 tests) y los específicos `/estadisticas/epas` (10 tests) y `/estadisticas/eell` (14 tests). Para los dos nuevos, cada bloque incluye: respuesta 200, estructura del JSON, comportamiento con BD vacía (ceros sin error), corrección de cálculos con fixture, y cabecera `Cache-Control`. Los tests más importantes son los de cálculo: nuevos vs recurrentes en EPAs (una entidad solo cuenta como nueva la primera vez que aparece), ratio de exclusión en EELL, la concentración top 10 % (los porcentajes deben sumar exactamente 100), la distribución por tramos de importe EELL y la recurrencia de entidades EELL (con un fixture multiaño donde una entidad repite en 2023 y 2024).

Incluye además el bloque de **exclusiones** de las estadísticas (nº por año + causas frecuentes del último año, con `db_exclusiones`) y el **resumen por convocatoria**: el endpoint público `GET /estadisticas/resumen-convocatorias` (estructura, recuento por estado e importe, y `Cache-Control`) y que su gemelo privado `GET /privado/resumen-tabla` sigue exigiendo login (401 sin token).

#### test_auth.py

Los tests más importantes. Cubren tres bloques:

- **Registro**: usuario nuevo se crea correctamente, email duplicado es rechazado (400), contraseña débil es rechazada por el validador Pydantic (422).
- **Login**: credenciales correctas devuelven token JWT; contraseña incorrecta o email inexistente devuelven 401.
- **Zona privada**: los endpoints `/privado/perfil` y `/privado/resumen-exclusivo` devuelven 401 sin token y 200 con token válido.

#### test_agrupaciones.py

Verifica el endpoint `/agrupaciones/{id_solic}`, que devuelve el desglose de municipios miembro de una agrupación EELL. Cubre los casos de error (ID inexistente, solicitud sin agrupación asociada) y el camino feliz con una fixture completa que construye toda la cadena de relaciones: Convocatoria → Beneficiario → Solicitud → Concesion → Agrupacion → AgrupacionMiembro.

Se añadieron dos tests al detectar bugs en el frontend (ver "Error 3" en pruebas manuales): uno verifica que `representante` es un objeto con campo `nombre` (y no una cadena o tipo incorrecto), y otro verifica que `importe_asignado` de cada miembro llega con el valor numérico correcto.

**Bug detectado por estos tests:** el router usaba `joinedload("miembros")` y `joinedload("representante")` con strings, que no están admitidos en SQLAlchemy 2.x. Los tests fallaron con `ArgumentError` en todos los entornos, lo que llevó a corregir el router para usar atributos de clase (`Agrupacion.miembros`, `Agrupacion.representante`).

#### test_avisos.py

Verifica el endpoint `/avisos/` añadido en la rama `9e`. Cubre tres casos principales: BD vacía devuelve lista vacía, solo se devuelven convocatorias del año en curso sin resolución (las que tienen `fecha_resolucion IS NULL`), y las convocatorias ya resueltas o de años anteriores quedan excluidas. Incluye una fixture que inserta tres convocatorias con distintas combinaciones de año y estado de resolución para cubrir los casos límite.

#### test_privado.py

Verifica el endpoint `PUT /privado/cambiar-contrasena`. Cubre los tres casos de error (sin token → 401, contraseña actual incorrecta → 401, nueva contraseña débil → 422) y el camino feliz completo: el cambio devuelve 200, el login con la contraseña nueva funciona, y el login con la contraseña vieja falla. Este último par de tests es el más importante: confirma que el hash en base de datos se actualizó realmente.

#### test_refresh_token.py

Verifica el sistema de refresh token implementado en la rama `9gh`. Cubre el ciclo completo: el login genera un token opaco de 64 caracteres, el refresh devuelve un nuevo access token y rota el refresh token (el anterior queda revocado), un token inventado o ya usado devuelve 401, y el logout revoca correctamente el token en la base de datos. El test de rotación es el más importante: garantiza que cada refresh token solo puede usarse una vez, lo que limita el daño si un token es interceptado. El séptimo test verifica que cambiar la contraseña revoca todos los refresh tokens activos del usuario — una medida de seguridad que impide que sesiones abiertas en otros dispositivos sigan activas tras un cambio de contraseña.

#### test_cache_headers.py

Verifica que los endpoints con datos raramente cambiantes incluyen la cabecera `Cache-Control` correcta. `/convocatorias/` recibe `public, max-age=86400` (1 día); `/estadisticas/` recibe `public, max-age=3600` (1 hora). La cabecera se inyecta en el router FastAPI mediante el parámetro `Response`, que FastAPI resuelve automáticamente como dependencia.

#### test_rate_limiting.py

Verifica la configuración de rate limiting en Nginx siguiendo el mismo patrón que `test_https_config.py`: lee `docker/nginx/default.conf` directamente sin necesitar Docker levantado. Comprueba que la zona `login` está definida con un límite de `10r/m`, que el status de rechazo es `429` y que el bloque de rate limiting está asociado únicamente a `/auth/login`.

#### test_logging.py

Verifica el sistema de logging implementado en la rama `9c`. Cubre dos partes:

- **Middleware de requests**: comprueba que cada petición HTTP queda registrada con método, ruta, código de respuesta e IP del cliente. Usa `caplog` de pytest para capturar los registros del logger `bdns` sin necesitar archivos en disco.
- **Configuración del logger**: verifica directamente la función `setup_logging()` y el `generic_exception_handler` usando mocks para no depender del sistema de archivos ni de llamadas HTTP reales.

#### test_recuperar_password.py

Verifica el flujo completo de recuperación de contraseña implementado en la rama `11b`. Cubre los dos endpoints nuevos:

- **`POST /auth/recuperar`**: comprueba que devuelve 200 tanto si el email existe como si no (para no revelar qué cuentas están registradas), que se crea un `ResetToken` en la BD, y que la función de envío de email se invoca con los parámetros correctos. En tests, `enviar_email_recuperacion` se mockea con `unittest.mock.patch` para no necesitar un servidor SMTP real.

- **`POST /auth/reset`**: cubre el camino feliz (token válido → contraseña cambiada → login funciona con nueva contraseña) y los tres casos de error: token inventado (400), token ya usado (400) y token expirado (400). El test de token expirado inserta directamente en la BD un `ResetToken` con `expira_en` en el pasado, sin necesidad de esperar 15 minutos reales.

#### test_verificacion_email.py

Cubre el flujo completo de verificación de email en el registro: el usuario se crea con `email_verificado=0`, se genera un token en `verificacion_tokens`, el login queda bloqueado hasta verificar, y `GET /auth/verificar?token=...` activa la cuenta. Incluye casos de token inválido, expirado y ya usado. Un test adicional verifica que completar el flujo de recuperación de contraseña también activa `email_verificado` (porque demostrar que recibes el email de reset equivale a demostrar que controlas esa dirección).

#### test_admin.py

Cubre el panel de administración completo: control de acceso (401 sin token, 403 con rol `registrado`), lectura del estado del sistema, CRUD de usuarios con las protecciones anti-autoedición (400 al intentar modificar la propia cuenta), gestión completa de avisos (listar, desactivar, reactivar, eliminar, protección 409 si hay solicitudes asociadas), y visor de logs de acceso y de error (`GET /admin/logs` y `GET /admin/logs/errores`). Detectó dos diferencias entre SQLite y MariaDB durante el desarrollo: `date(2025, 1, 1)` como tipo Python en lugar de string para columnas DATE, y `tipo_benef="asociacion"` (valor ENUM válido) en lugar de `"epa"`.

#### test_check_bdns.py

Verifica el helper `_get_bdns_con_retry` del script `docker/cron/scripts/check_bdns.py`, que centraliza los reintentos con backoff exponencial (2s → 4s → 8s) en las llamadas a la API BDNS. Cubre cinco casos: primer intento OK (sin sleeps), recuperación tras un fallo puntual, abandono tras 3 errores de red, abandono tras 3 respuestas 500 y verificación de que el patrón de espera es exponencial.

Los tests mockean `requests.get` y `time.sleep` para no esperar tiempo real ni golpear la API. El módulo se carga con `importlib.util` porque `docker/cron/scripts/` no es un paquete Python y porque tiene side effects al importarse (creación de logs en `/app/logs/cron` y llamada a `logging.basicConfig`) que se neutralizan con `unittest.mock.patch`. Además, `pymysql` se sustituye en `sys.modules` por un mock porque solo se instala en el contenedor cron, no en el venv local.

#### test_scheduler.py

Verifica el calendario completo del scheduler del cron (`docker/cron/scheduler.py`), que antes no tenía cobertura. Comprueba que `_jobs_for(dt)` devuelve los scripts correctos en función de la fecha y hora UTC. Cubre tres bloques:

- **`health_check.py`**: corre cada 6 horas (00:00, 06:00, 12:00, 18:00) los 365 días del año, y nunca fuera del minuto 0.
- **`check_bdns.py` — temporada convocatorias (marzo–junio)**: marzo y junio cada 4 días; abril y mayo cada 2 días; siempre a las 08:00 UTC.
- **`check_bdns.py` — temporada resoluciones (noviembre–enero)**: noviembre y diciembre cada 2 días; enero cada 4 días.

Incluye además casos negativos (fuera de temporada, horas distintas a 08:00, días no múltiplos del intervalo) y combinaciones realistas (un mismo instante puede activar `health_check`, `check_bdns` o ninguno).

Es el primer archivo del proyecto que usa `@pytest.mark.parametrize`: 21 funciones de test se expanden a 119 ejecuciones independientes, una por cada fecha probada. Carga el módulo con `importlib.util` porque `docker/cron/` no es un paquete Python (sin `__init__.py`).

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

**Corrección:** se actualizaron los 17 `value` del select en `buscador.html` para que coincidan exactamente con los valores de la BD. Algunos casos especiales:

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

---

## Pruebas manuales — agrupaciones, tramos y UX (rama 10a)

Realizadas con Docker levantado en `https://localhost`.

### Bugs corregidos en esta rama

#### Error 3 — Ficha de agrupación mostraba `[object Object]` e importes vacíos

**Detectado en:** prueba manual de la ficha de entidad para un ayuntamiento miembro de una agrupación EELL 2025.

**Síntoma 1:** el campo "Entidad representante" mostraba `[object Object]` en lugar del nombre del ayuntamiento.

**Causa:** el backend devuelve `representante` como objeto `{id_benef, nombre, cif, tipo_benef}`. En `entidad.js` se pintaba directamente `datos.representante` en un template literal, lo que convierte cualquier objeto a su representación string `[object Object]`.

**Corrección:** `datos.representante` → `datos.representante?.nombre`.

**Síntoma 2:** la columna "Importe asignado (€)" mostraba `—` para todos los miembros de la agrupación aunque la BD tenía valores reales.

**Causa:** el schema `MiembroAgrupacionOut` usa el campo `importe_asignado`, pero `entidad.js` buscaba `m.importe` (nombre incorrecto).

**Corrección:** `m.importe` → `m.importe_asignado` en el renderizado de la tabla de miembros.

**Tests añadidos:** entradas 145 y 146 de la tabla.

---

### Flujos verificados (rama 10a)

| # | Pantalla | Acción | Resultado esperado | OK |
|---|----------|--------|-------------------|-----|
| 14 | Buscador | Buscar EELL 2025 concedidas | Aparecen badges `T1`, `T2`, `T3` junto al nombre de cada entidad; la leyenda de tramos se muestra encima de la tabla | ✔ |
| 15 | Buscador | Buscar EPA o EELL de otro año | No aparecen badges de tramo ni leyenda | ✔ |
| 16 | Ficha entidad | Entidad EELL 2025 concedida con tramo | Badge `T1`/`T2`/`T3` visible junto al importe en la fila correspondiente; leyenda visible encima de la tabla | ✔ |
| 17 | Ficha entidad | Entidad miembro de agrupación EELL | "Entidad representante" muestra el nombre correcto (no `[object Object]`); importes asignados visibles para cada miembro | ✔ |
| 18 | Buscador | Buscar con filtros → clic en una fila → botón "Volver al buscador" | Los filtros y resultados se restauran exactamente igual que antes de entrar en la ficha | ✔ |
| 19 | Buscador | Abrir ficha desde una búsqueda → pulsar Atrás del navegador | Mismo comportamiento que el botón "Volver al buscador" | ✔ |
| 20 | Buscador | Limpiar filtros | La URL vuelve a `buscador.html` sin parámetros | ✔ |
| 21 | Ficha entidad | Acceder directamente a `entidad.html?cif=X` sin historial previo | El botón "Volver al buscador" redirige a `buscador.html` | ✔ |
| 22 | Buscador | Descargar CSV con filtros de provincia y línea activos | El archivo CSV contiene solo los registros filtrados (bug previo: estos filtros se ignoraban en la exportación) | ✔ |
| 23 | Buscador | Verificar campo `tramo` en la respuesta de la API | `curl -sk "https://localhost/solicitudes/?tipo=eell&anio=2025&estado=concedida&limite=1" \| python3 -c "import sys,json; d=json.load(sys.stdin); print(d['resultados'][0]['tramo'])"` → imprime `1`, `2` o `3` | ✔ |
| 24 | Home | Cargar `index.html` con Docker levantado | Aparece el bloque "Convocatorias" debajo de los KPIs con dos columnas: EELL y EPA, cada una con sus años, fechas y botones "Ver →" | ✔ |
| 25 | Home | Clic en "Ver →" de EPA 2025 | Abre el buscador con filtros `tipo=epa&anio=2025` pre-aplicados y resultados cargados | ✔ |
| 26 | Home | Fila 2026 EELL | Muestra fecha "8 abr 2026" y texto "Pendiente de resolución" en cursiva (sin botón Ver) | ✔ |
| 27 | Home | Verificar fechas de convocatoria en la API | `curl -sk "https://localhost/convocatorias/" \| python3 -c "import sys,json; [print(c['tipo_convoc'], c['anio_convocatoria'], c['fecha_convocatoria']) for c in json.load(sys.stdin)]"` → muestra fechas reales para todas las convocatorias excepto 2026 EELL que ya las tenía | ✔ |

---

## Pruebas manuales — recuperación de contraseña (rama 11b)

Realizadas con Docker levantado. Mailpit accesible en `http://localhost:8025`.

### Flujo principal

| # | Pantalla | Acción | Resultado esperado | OK |
|---|----------|--------|-------------------|-----|
| 28 | Login | Clic en "¿Olvidaste tu contraseña?" | Navega a `recuperar-password.html` | ✔ |
| 29 | Recuperar contraseña | Introducir email registrado y pulsar "Enviar enlace" | El formulario desaparece y aparece el mensaje "Si ese email está registrado, recibirás un enlace en breve"; en Mailpit aparece el email con el enlace | ✔ |
| 30 | Mailpit | Abrir el email recibido | Muestra remitente `noreply@subvencionesDGDA.local`, asunto correcto y enlace con token en el cuerpo | ✔ |
| 31 | Reset password | Copiar el enlace del email, abrirlo en el navegador, introducir contraseña válida y pulsar "Guardar" | Mensaje de éxito verde y aparece el enlace "Ir a iniciar sesión" | ✔ |
| 32 | Login | Iniciar sesión con la nueva contraseña | Login correcto, accede a la zona privada | ✔ |

### Casos límite verificados

| # | Prueba | Cómo realizarla | Resultado esperado | OK |
|---|--------|-----------------|-------------------|-----|
| 33 | Token inventado → 400 | `curl -sk -X POST https://subvencionesDGDA.local/auth/reset -H "Content-Type: application/json" -d '{"token":"tokenfalso123","contrasena_nueva":"Nueva1234"}'` | `{"error": 400, "mensaje": "Enlace inválido o expirado"}` | ✔ |
| 34 | Token ya usado → 400 | Abrir el enlace del email en el navegador por segunda vez, introducir contraseña válida y enviar; verificar en F12 → Network | Status 400, mensaje "Enlace inválido o expirado" en la página y en Response del DevTools | ✔ |
| 35 | Contraseña débil → 422 | `curl -sk -X POST https://subvencionesDGDA.local/auth/reset -H "Content-Type: application/json" -d '{"token":"cualquiera","contrasena_nueva":"debil"}'` | `{"error": 422, "mensaje": "Datos de entrada inválidos"}` | ✔ |
| 36 | Contraseñas no coinciden → validación frontend | Abrir `reset-password.html?token=inventado`, introducir contraseñas distintas y pulsar "Guardar" | Mensaje de error "Las contraseñas no coinciden" sin petición de red al backend (visible en F12 → Network: sin POST a `/auth/reset`) | ✔ |
| 37 | Token expirado → 400 | Abrir el enlace de un email pedido hace más de 15 minutos, introducir contraseña válida y pulsar "Guardar" | Status 400, mensaje "Enlace inválido o expirado" en la página y en F12 → Network → Response | ✔ |
