# Estrategia de tests

El proyecto tiene dos capas de tests con propósitos distintos.

---

## Qué se testea y por qué

### 1. Endpoints del backend (`test_smoke`, `test_convocatorias`, `test_solicitudes`, `test_estadisticas`, `test_auth`, `test_recuperar_password`)

Verifican que la API HTTP funciona correctamente: códigos de respuesta, estructura del JSON, filtros, paginación y autenticación JWT.

Usan **SQLite en memoria** (configurado en `conftest.py`) en lugar de la MariaDB real, lo que permite ejecutar los tests sin Docker ni datos cargados. Cada test parte de una BD limpia.

### 2. Parser EPA 2025 (`test_parser_epa2025`)

Verifica las funciones puras del parser antes de que lleguen a la BD. Son tests de **caja blanca**: conocemos la lógica interna y probamos los casos límite que causaron bugs reales.

| Test | Qué protege |
|---|---|
| `test_mapear_indices_concedido_entidad_no_es_entidad` | La columna "Concedido entidad – Euros" no sobreescribe el índice de la columna Entidad |
| `test_extraer_entidad_fallback_*` | El fallback heurístico recupera el nombre real cuando el índice apunta al importe |
| `test_estado_anexo_iv_es_denegada_no_concedida` | El ANEXO IV ("no adquieren la condición de beneficiarias") no se clasifica como `concedida` |
| `test_linea_extraida_en_concedidas` | La línea de actuación se extrae y normaliza correctamente |

El test de estado usa `unittest.mock` para simular la respuesta HTTP del BOE con un XML mínimo, sin necesidad de conexión a internet.

### 3. Normalización del dataset unificado (`test_unificar_datasets`)

Verifica las funciones de transformación de `unificar_datasets.py`. Son funciones puras (sin I/O) que se pueden testear de forma completamente aislada.

| Función | Qué se verifica |
|---|---|
| `normalizar_estado_epa` | `denegada` → `excluida` (2021–2023) o `no_beneficiaria` (2024–2025) |
| `normalizar_estado_eell` | `concedida` con importe 0 → `no_beneficiaria` |
| `limpiar_importe` | `None`, cadena vacía o valor no numérico → `0.0` |
| `limpiar_entidad` | `None`, vacío o la cadena `"None"` → `None` |

---

## Qué no se testea y por qué

### `cargar_dataset.py`

Este script carga el dataset unificado en MariaDB. No tiene tests por dos razones:

1. **Es lógica de inserción, no de transformación.** Su única responsabilidad es hacer INSERTs e IGNOREs correctamente. Los datos que inserta ya han sido validados por los tests del parser y del unificador.

2. **Requeriría una MariaDB real.** A diferencia del backend (que usa SQLite en memoria como sustituto), `cargar_dataset` usa características específicas de MariaDB (`ON DUPLICATE KEY`, tipos `ENUM`, `DECIMAL`) que SQLite no reproduce fielmente. Testear con una MariaDB real en CI añadiría complejidad de infraestructura desproporcionada para un script que se ejecuta manualmente una sola vez por convocatoria.

### Parsers de años anteriores y EELL

Los parsers EPA 2021–2024 y EELL (PDF y BOE) no tienen tests unitarios. Sus funciones de extracción son más simples o dependen de `pdfplumber` (difícil de mockear). La validación de sus datos se hace empíricamente comparando los totales con los publicados en el BOE.

---

## SQLite vs MariaDB: diferencias conocidas y límite de los tests

Los tests de endpoints usan SQLite en memoria como sustituto de MariaDB. SQLite acepta los mismos modelos SQLAlchemy y funciona bien para probar lógica de aplicación, pero no replica el comportamiento de MariaDB en tres puntos concretos que este proyecto usa:

| Característica | MariaDB (producción) | SQLite (tests) |
|---|---|---|
| `ENUM` en columnas | Rechaza valores fuera del enum a nivel de BD | Lo acepta como texto cualquiera |
| `DECIMAL(12,2)` | Precisión fija, redondea al guardar | Se trata como float de Python |
| `ON DUPLICATE KEY UPDATE` | Sintaxis nativa para upserts | No existe, hay que reescribirlo |

**Por qué no es un problema para los tests actuales:** los tests de endpoints no comprueban que la BD rechace un valor de `ENUM` inválido — esa validación la hace SQLAlchemy y FastAPI antes de llegar a la BD. Tampoco dependen de la precisión exacta de `DECIMAL`. Y ningún test usa `ON DUPLICATE KEY` directamente (eso solo lo usa `cargar_dataset.py`).

En la práctica los tests prueban **lógica de la aplicación** (filtros, respuestas HTTP, autenticación), no **integridad de la BD**. Para lo primero, SQLite es suficiente.

**Si en el futuro se quisiera testear algo que dependa de estas diferencias** (por ejemplo, que la API rechaza un estado inválido a nivel de BD, o que `cargar_dataset` hace el upsert correctamente), habría que:

1. Añadir un servicio MariaDB al entorno de tests, ya sea levantando un contenedor Docker específico para tests o usando GitHub Actions con un `service` de MariaDB en el pipeline de CI.
2. Crear un segundo `conftest.py` o una fixture separada que apunte a esa MariaDB de test en lugar de a SQLite.
3. Marcar esos tests con `@pytest.mark.integration` para poder ejecutarlos por separado de los tests rápidos que no necesitan Docker.

Ese patrón (tests unitarios rápidos con SQLite + tests de integración con MariaDB real en CI) es el estándar en proyectos profesionales con FastAPI y bases de datos relacionales.

---

## Cómo ejecutar los tests

```bash
# Todos los tests
python -m pytest tests/

# Solo los nuevos (pipeline de datos)
python -m pytest tests/test_parser_epa2025.py tests/test_unificar_datasets.py -v

# Solo los tests de endpoints
python -m pytest tests/test_smoke.py tests/test_solicitudes.py tests/test_auth.py tests/test_estadisticas.py tests/test_convocatorias.py -v

# Solo los tests de recuperación de contraseña
python -m pytest tests/test_recuperar_password.py -v
```

No es necesario tener Docker activo para ejecutar ninguno de estos tests. Los tests de `test_recuperar_password.py` usan `unittest.mock.patch` para simular el envío de email — no necesitan Mailpit levantado.
