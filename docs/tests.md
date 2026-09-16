# Tests — estrategia y resultados

El proyecto tiene dos niveles de pruebas:

| Nivel | Cantidad | Herramienta |
|-------|----------|-------------|
| Tests automáticos | 493 funciones / 657 ejecuciones | pytest (sin Docker) |
| Pruebas manuales | 52 | Navegador + DevTools con Docker levantado |
| **Total** | **493 funciones / 657 ejecuciones**, más 52 pruebas manuales | |

Las pruebas manuales se distribuyen en seis bloques: 6 de HTTPS/infraestructura, 13 de flujos del frontend, 10 de endpoints de la API vía `/docs`, 2 de caché y rate limiting, 14 de las funcionalidades nuevas de rama 10 (agrupaciones, tramos, URL persistence y bloque convocatorias en Home) y 6 de recuperación de contraseña (rama 11b).

Nota sobre ejecución: **las 657 pasan sin Docker**. `test_https_config.py` y `test_rate_limiting.py` llegaron a necesitarlo, pero se reescribieron para comprobar los ficheros de configuración directamente, que es más rápido y no depende de tener el entorno levantado.

---

## Sobre el conteo de tests

A partir del archivo `test_scheduler.py` (verificación del calendario del cron) el proyecto incluye tests parametrizados. Pytest cuenta cada caso parametrizado como una ejecución independiente, por lo que el número de **ejecuciones** (657) es mayor que el número de **funciones de test** escritas (493). Ejemplo:

```python
@pytest.mark.parametrize("day", [1, 5, 9, 13, 17, 21, 25, 29])
def test_check_bdns_corre_en_marzo_cada_4_dias(day):
    assert "check_bdns.py" in _jobs_for(_dt(2026, 3, day, 8, 0))
```

Esa es **una función**, pero pytest la ejecuta 8 veces (una por cada día) y reporta 8 PASSED. `@pytest.mark.parametrize` es una técnica estándar de pytest para evitar duplicar código de test cuando solo cambian los datos de entrada.

`test_scheduler.py` y `test_accesibilidad_modales.py` usan `parametrize`: el primero recorre días y meses del calendario del cron (24 funciones → 169 ejecuciones), el segundo repite la misma comprobación sobre los tres modales (3 → 7). Los otros 37 archivos tienen correspondencia 1:1 entre funciones de test y ejecuciones.

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

El proyecto incluye **493 funciones de test automáticas** (657 ejecuciones con pytest) distribuidas en 42 archivos que cubren la API REST, el sistema de autenticación, el panel de administración, la verificación de email, los refresh tokens, el formulario de contacto, el modo mantenimiento, el estado del plazo de las convocatorias, el pipeline de datos, los parsers, el sistema de logging, la configuración HTTPS, el endpoint de avisos, las cabeceras de caché, la configuración de rate limiting, el scheduler del cron, el helper de reintentos a la API BDNS, **el correo saliente** (STARTTLS, credenciales y enlaces de los correos) y **el despliegue con secretos propios** (credenciales fuera de los ficheros versionados y puertos de administración atados a la interfaz local).

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

### Tests por archivo

En lugar de una tabla fila a fila (que se desincronizaba cada vez que se añadía
un test), este resumen se **deriva de la propia suite** y se regenera en segundos:

```bash
pytest tests/ --collect-only -q            # lista todos los tests recogidos
pytest tests/ --collect-only -q | grep -c "::"   # total de ejecuciones (657)
```

Recuento por archivo (**funciones** escritas / **ejecuciones** de pytest; solo
difieren en `test_scheduler.py`, que usa `@pytest.mark.parametrize`):

| Archivo | Func. | Ejec. | Qué cubre |
|---|---:|---:|---|
| `test_smoke.py` | 3 | 3 | Humo: `GET /` responde y la app arranca |
| `test_convocatorias.py` | 4 | 4 | `GET /convocatorias/` (lista, BD vacía, `Cache-Control`) |
| `test_solicitudes.py` | 22 | 22 | Buscador: filtros, paginación, búsqueda, export CSV y **causas de exclusión** (filtro por token, catálogo `/solicitudes/causas`) |
| `test_estadisticas.py` | 37 | 37 | `/estadisticas/`, `/epas`, `/eell`: cálculos, umbrales, tramos, recurrencia, **exclusiones** y **resumen por convocatoria** (público + privado protegido) |
| `test_agrupaciones.py` | 7 | 7 | `GET /agrupaciones/{id}`: miembros de agrupaciones EELL |
| `test_avisos.py` | 11 | 11 | `/avisos/`: convocatorias del año en curso sin resolución |
| `test_cache_headers.py` | 4 | 4 | Cabeceras `Cache-Control` en los endpoints públicos |
| `test_auth.py` | 10 | 10 | Login, JWT y validación de contraseña (el alta vive en `test_admin.py`) |
| `test_refresh_token.py` | 7 | 7 | Rotación y revocación del refresh token |
| `test_verificacion_email.py` | 7 | 7 | Verificación de email por token |
| `test_recuperar_password.py` | 9 | 9 | Flujo de recuperación/reset de contraseña |
| `test_privado.py` | 6 | 6 | Zona privada: perfil, cambiar nombre/contraseña, `resumen-tabla` protegido |
| `test_admin.py` | 46 | 46 | Panel admin: **alta de usuarios**, listado paginado, cambio de rol/activo, logs de la app y del cron |
| `test_contacto.py` | 9 | 9 | Formulario de contacto: honeypot, rate limiting, validación, error SMTP |
| `test_despliegue_secretos.py` | 10 | 10 | Despliegue con secretos propios: credenciales fuera de los ficheros versionados y puertos de administración solo en local |
| `test_smtp_config.py` | 22 | 22 | Correo saliente: STARTTLS, credenciales, `SITE_URL` de los enlaces y valores por defecto de Mailpit |
| `test_mantenimiento.py` | 4 | 4 | Modo mantenimiento (503 controlado) |
| `test_unificar_datasets.py` | 51 | 51 | Pipeline: unificación, deduplicación cross-year, provincia/CCAA desde CIF, estados |
| `test_parser_epa2025.py` | 22 | 22 | Parser EPA 2025 (extracción heurística) y captura de causas |
| `test_parser_epa_admitidas_2024.py` | 10 | 10 | Parser de la línea EPA 2024 (anclaje por CIF, nombres con "COLONIAS") |
| `test_check_bdns.py` | 5 | 5 | Comprobación BDNS del cron y reintentos con backoff |
| `test_scheduler.py` | 24 | 169 | Calendario del cron (parametrizado por días del mes y por meses) |
| `test_health_check.py` | 15 | 15 | Aviso de caída: que salga **un solo correo** por incidente, que avise al recuperarse, que detecte una base de datos caída aunque el proceso viva, y que ni un fallo de correo ni uno de escritura tumben la comprobación |
| `test_conexion_bd.py` | 3 | 3 | Salud del pool de conexiones: que el motor no pueda volver a crearse sin `pool_pre_ping`, y que `pool_recycle` quede por debajo del `wait_timeout` de MariaDB. Es la causa raíz de la caída del 7-8 de septiembre de 2026 |
| `test_logging.py` | 10 | 10 | Logging de la aplicación y **formato de los registros de Nginx** (procedencia y dispositivo, declarados en la política de privacidad) |
| `test_backup_db.py` | 11 | 11 | Copias de seguridad: credenciales del `.env`, descarte de volcados incompletos y rotación |
| `test_nginx_tls.py` | 12 | 12 | Configuración TLS de Nginx: ruta del reto ACME antes de la redirección y rutas del certificado fuera del fichero versionado |
| `test_https_config.py` | 9 | 9 | TLS/HTTPS y redirección (comprueba los ficheros, sin Docker) |
| `test_rate_limiting.py` | 6 | 6 | Rate limiting de Nginx (comprueba la configuración, sin Docker) |
| `test_css_indice.py` | 4 | 4 | Que el índice de secciones de `styles.css` refleje el cuerpo del archivo |
| `test_mapa_ccaa.py` | 7 | 7 | Que el tooltip de Leaflet no se enlace en táctil: enlazarlo y deshacerlo dejaba escuchadores huérfanos que reventaban al tocar el mapa |
| `test_accesibilidad_modales.py` | 3 | 7 | Que el foco salga de un modal **antes** de marcarlo `aria-hidden`: si un descendiente lo conserva, el navegador rechaza el atributo y el modal sigue anunciándose |
| `test_nginx_canonico.py` | 6 | 6 | Una sola dirección: `www` y `/index.html` redirigen, y la portada NO (un 301 ahí sería un bucle) |
| `test_recursos_documentos.py` | 12 | 12 | Listado de recursos: título enlazado y descripción, ninguna URL partida en dos líneas, la vía estatal distinguida de la autonómica, y que los PDF propios existen de verdad en `assets/docs/` y no solo enlazados |
| `test_favicon.py` | 4 | 4 | Que exista un `favicon.ico` de verdad en la raíz —con cabecera ICO y los tamaños de 16 y 32 px—, y que Nginx le siga poniendo caché larga |
| `test_estudio_ayuntamientos.py` | 12 | 12 | Bloque del estudio municipal y cierre de la portada: cada porcentaje con su base, y las anclas fuera del alcance de la barra fija |
| `test_informe_visitas.py` | 20 | 20 | Informes de visitas: formato de log a la par con Nginx, robots y centros de datos descontados sin tocar operadoras de consumo, y que los informes no acaben publicados |
| `test_robots_sitemap.py` | 11 | 11 | `robots.txt`, `sitemap.xml` y canónicas, y que los tres textos que permiten el rastreo de IA sigan diciendo lo mismo |
| `test_aclaracion_no_oficial.py` | 4 | 4 | Que todas las páginas con pie aclaren que el sitio no es oficial |
| `test_navbar_paginas.py` | 3 | 3 | Que toda página con botón de menú cargue `navbar.js`: seis lo mostraban sin cargarlo y no hacía nada |
| `test_bloque_bdns_portada.py` | 6 | 6 | Que el bloque de la BDNS en la portada no falle en silencio: nace `hidden` y la cifra la calcula el JS, así que un id o un campo renombrado lo dejarían invisible sin dar error |
| `test_deteccion_convocatorias.py` | 5 | 20 | Qué convocatorias de la BDNS son las de este proyecto: premios, certámenes y otras líneas quedan fuera, y las dos copias del detector (pipeline y cron) clasifican igual |
| **Total** | **493** | **657** | 42 archivos |

> Para el detalle de qué comprueba cada archivo, ver la sección siguiente
> ("Descripción por módulo"). Al añadir tests, basta con actualizar el recuento
> de la fila correspondiente (o regenerarlo con `--collect-only`).


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

- **`health_check.py`**: corre **cada media hora** (minutos 0 y 30) los 365 días del año. Los tests cubren además el aviso por correo: que salga uno al caer, **ninguno más mientras siga caída** —96 comprobaciones en dos días serían 96 correos—, uno al recuperarse, y que un fallo al enviarlo o al escribir el log no tumbe la comprobación.
- **`check_bdns.py` — temporada convocatorias (marzo–junio)**: marzo y junio cada 4 días; abril y mayo cada 2 días; siempre a las 08:00 UTC.
- **`check_bdns.py` — temporada resoluciones (noviembre–enero)**: noviembre y diciembre cada 2 días; enero cada 4 días.

Incluye además casos negativos (fuera de temporada, horas distintas a 08:00, días no múltiplos del intervalo) y combinaciones realistas (un mismo instante puede activar `health_check`, `check_bdns` o ninguno).

Fue el primer archivo del proyecto en usar `@pytest.mark.parametrize`: 24 funciones de test se expanden a **169 ejecuciones** independientes, una por cada fecha probada. Carga el módulo con `importlib.util` porque `docker/cron/` no es un paquete Python (sin `__init__.py`).

#### test_unificar_datasets.py

Prueba las funciones puras de transformación de `unificar_datasets.py`. Dos casos relevantes:

- `normalizar_estado_epa` mapea "denegada" a valores distintos según el año (≤2023 → `excluida`; ≥2024 → `no_beneficiaria`), porque el BOE usa la misma palabra para dos realidades distintas.
- `resolver_anio_epa` decide si un registro es una **resolución tardía** que hay que atribuir a la convocatoria del año anterior. Los tests cubren los dos casos que sí se reatribuyen (La Sexta Huella y Amibichos) y, sobre todo, los dos falsos positivos que **no** deben reatribuirse: el número de expediente reutilizado por otra entidad (`SUBV2022021`) y la errata de año (`SUBV2032021`). Sin la comprobación del CIF, ambos colapsarían bajo la misma clave de deduplicación.

#### test_parser_epa2025.py

Prueba las funciones del parser EPA 2025 con XMLs mínimos generados en memoria (sin conexión a internet). Documenta dos bugs históricos resueltos:

- `mapear_indices`: la columna "Concedido entidad – Euros" sobreescribía el índice de la columna Entidad. Ahora va a `importe_idx`.
- `extraer_entidad_2025`: cuando el índice apuntaba al importe en lugar del nombre, el fallback heurístico recupera el nombre real recorriendo las celdas.

#### test_bloque_bdns_portada.py

Protege el bloque del cierre de la portada que cuenta cuántas concesiones nunca se comunicaron a la Base de Datos Nacional de Subvenciones.

Existe por un motivo concreto: ese bloque **falla de forma invisible**. El párrafo de la cifra nace con `hidden` y solo se muestra si `pintarCifraBdns()` encuentra sus `id` y consigue sumar los campos de `/estadisticas/resumen-convocatorias`. Si algo se rompe no hay hueco, ni error en consola, ni un 500: simplemente el dato deja de estar, y eso no se detecta mirando la página.

Se comprueban los tres puntos de rotura reales: que los `id` del HTML sigan siendo los que busca el JS, que el endpoint siga exponiendo `concedidas` e `importe_total`, y que la convocatoria EPA 2022 siga declarada en `CONVOCATORIAS_EN_BDNS` —sus 592 concesiones sí se comunicaron, y si se cayera de esa lista la web pasaría a afirmar que no se comunicó ninguna—.

No se comprueba el número en sí: sale de la base de datos y cambia cuando entra un año nuevo. Lo que se verifica es que la maquinaria que lo calcula sigue conectada.

Dos comprobaciones más, sobre cómo se presenta el dato: que el número lleve **punto de millar** (en español los de cuatro cifras no lo llevan, y «2030 concesiones» rodeado de años se lee como si fuera uno), y que la cifra **no se presente como el total absoluto** — excluye una concesión de 4.684,91 € de 2022 que la BDNS tampoco tiene, así que decir «en total» contradiría al párrafo siguiente de la propia página.

#### test_deteccion_convocatorias.py

Fija qué convocatorias de la API BDNS son las que recoge este proyecto y cuáles no. La búsqueda por descripción devuelve también premios, certámenes artísticos y otras líneas de subvención de la misma Dirección General.

Cubre las **dos copias** del detector —`bdns_lookup._detectar_tipo` y `check_bdns.detectar_tipo`, duplicadas a propósito porque la carga y el cron no comparten código— con los títulos literales que devuelve la API, e incluye un test de que ambas clasifican igual: si se toca una y no la otra, salta.

El riesgo que cubre es asimétrico, y por eso el detector prefiere descartar: clasificar de menos hace que la carga caiga al respaldo de `_FECHAS` y que el cron registre «Tipo no detectado — Omitida», dos fallos visibles; clasificar de más escribe el número, la fecha y el título equivocados en la base, o da de alta una convocatoria que no toca, sin que nadie se entere.

El último test es una segunda red sobre `cargar_indice_bdns()`: aunque el detector fallara, dos convocatorias en la misma clave `(año, tipo)` deben avisar y conservar la primera, en vez de que la última gane en silencio.

#### test_recursos_documentos.py — los PDF propios

Comprobación añadida al incorporar documentos propios a Recursos. Existe porque
el fallo típico aquí no es de código: el HTML enlaza `assets/docs/loquesea.pdf`,
el fichero se queda sin subir al repo y el enlace devuelve un 404 que nadie ve
hasta que alguien lo pulsa. El test recorre los nombres declarados, exige que
estén enlazados desde el bloque, que el fichero exista, que pese algo razonable
y que empiece por `%PDF-`.

#### test_favicon.py

Nace de un dato del informe de visitas de septiembre de 2026: **224 peticiones a
`/favicon.ico` devolviendo 404** en treinta días. Las páginas declaran
`<link rel="icon" href="assets/img/logo.png">`, pero navegadores, lectores de RSS
y buscadores piden `/favicon.ico` a la raíz de todas formas, y allí no había
nada.

Es el tipo de fallo que dura meses porque **no rompe nada visible**: la web se ve
igual, nadie recibe un error, solo se ensucia el registro. Se detectó mirando el
apartado «rutas que no existen» del informe, donde casi todo es ruido de sondeos
automáticos —y por eso el propio informe avisa de que ahí solo preocupa lo que
sea tuyo.

Se comprueba que el fichero existe en la raíz y no en `assets/`, que tiene
cabecera ICO de verdad (renombrar un PNG no vale: parte de los clientes que
piden esa ruta son justamente los que no interpretan PNG), que lleva los tamaños
de 16 y 32 px, y que la regla de Nginx con `expires 1y` sigue incluyendo la
extensión `.ico`.

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
| 1 | Inicio | Carga de métricas del dashboard | Números correctos (6396 solicitudes, 8 convocatorias, etc.) | ✔ |
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
