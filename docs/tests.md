# Tests automáticos — pytest

El proyecto incluye 23 tests automáticos que verifican los endpoints de la API REST y el sistema de autenticación.

## Cómo funcionan

En vez de conectarse a la base de datos real (MariaDB en Docker), los tests usan una base de datos **SQLite en memoria** que se crea antes de cada test y desaparece al terminar. Esto permite ejecutarlos en cualquier momento sin depender de Docker.

La configuración compartida está en `tests/conftest.py`:
- Crea un motor SQLite con `StaticPool` (todas las conexiones comparten la misma BD en memoria)
- Sustituye la dependencia `get_db` de FastAPI para que apunte a SQLite en vez de MariaDB
- Expone los fixtures `client` (cliente HTTP de prueba) y `db` (sesión de BD para insertar datos de prueba)

## Ejecutar los tests

```bash
source venv/bin/activate
pytest -v                          # todos los tests
pytest tests/test_auth.py -v      # solo un archivo
pytest -k "filtro"                 # solo tests cuyo nombre contiene "filtro"
```

## Tabla completa de tests

| # | Archivo | Tipo | Caja | Qué comprueba |
|---|---|---|---|---|
| 1 | `test_smoke.py` | Smoke | Negra | `GET /` responde 200 con `{"mensaje": "API funcionando"}` |
| 2 | `test_convocatorias.py` | Funcional | Negra | `GET /convocatorias/` responde 200 |
| 3 | `test_convocatorias.py` | Funcional | Negra | La respuesta es una lista JSON |
| 4 | `test_convocatorias.py` | Funcional | Negra | Con BD vacía devuelve `[]` sin error (robustez) |
| 5 | `test_solicitudes.py` | Funcional | Negra | `GET /solicitudes/` responde 200 |
| 6 | `test_solicitudes.py` | Funcional | Negra | La respuesta es una lista JSON |
| 7 | `test_solicitudes.py` | Funcional | Blanca | Filtro `?tipo=epa` devuelve solo las solicitudes EPA |
| 8 | `test_solicitudes.py` | Funcional | Blanca | Filtro `?estado=concedida` devuelve solo las concedidas |
| 9 | `test_solicitudes.py` | Funcional | Blanca | Paginación: `limite=2` da 2 en pág. 1 y 1 en pág. 2 |
| 10 | `test_estadisticas.py` | Funcional | Negra | `GET /estadisticas/` responde 200 |
| 11 | `test_estadisticas.py` | Funcional | Negra | El JSON tiene las 4 claves esperadas |
| 12 | `test_estadisticas.py` | Funcional | Blanca | Totales calculados correctos con datos reales |
| 13 | `test_estadisticas.py` | Funcional | Blanca | Desglose por año y tipo correcto |
| 14 | `test_auth.py` | Funcional | Blanca | Registro válido devuelve 201 con email y rol |
| 15 | `test_auth.py` | Funcional | Blanca | Registro con email duplicado devuelve 400 |
| 16 | `test_auth.py` | Unitario | Blanca | Contraseña débil rechazada con 422 (validador Pydantic) |
| 17 | `test_auth.py` | Funcional | Blanca | Login correcto devuelve token JWT con `token_type: bearer` |
| 18 | `test_auth.py` | Funcional | Blanca | Login con contraseña incorrecta devuelve 401 |
| 19 | `test_auth.py` | Funcional | Blanca | Login con email inexistente devuelve 401 |
| 20 | `test_auth.py` | Seguridad | Blanca | `GET /privado/perfil` sin token devuelve 401 |
| 21 | `test_auth.py` | Seguridad | Blanca | `GET /privado/perfil` con token válido devuelve 200 |
| 22 | `test_auth.py` | Seguridad | Blanca | `GET /privado/resumen-exclusivo` sin token devuelve 401 |
| 23 | `test_auth.py` | Seguridad | Blanca | `GET /privado/resumen-exclusivo` con token válido devuelve 200 |

## Descripción por módulo

### test_smoke.py
Comprueba lo más básico: que la API arranca y responde. Si este test falla, algo fundamental está roto.

### test_convocatorias.py
Verifica que `/convocatorias/` responde correctamente, que devuelve una lista JSON y que no da error cuando la base de datos está vacía (devuelve `[]`, no un fallo 500).

### test_solicitudes.py
Inserta 3 solicitudes de prueba (2 EPA y 1 EELL, 2 concedidas y 1 excluida) y comprueba que los filtros por tipo y estado funcionan correctamente. También prueba la paginación con `limite` y `pagina`.

### test_estadisticas.py
Verifica que el endpoint de estadísticas responde, que el JSON tiene la estructura esperada y que los cálculos de totales e importes son correctos con datos reales.

### test_auth.py
Los tests más importantes. Cubren tres bloques:

- **Registro**: usuario nuevo se crea correctamente, email duplicado es rechazado (400), contraseña débil es rechazada por el validador Pydantic (422).
- **Login**: credenciales correctas devuelven token JWT; contraseña incorrecta o email inexistente devuelven 401.
- **Zona privada**: los endpoints `/privado/perfil` y `/privado/resumen-exclusivo` devuelven 401 sin token y 200 con token válido.

## Tipos de test utilizados

- **Smoke**: verifica que el sistema arranca y responde mínimamente.
- **Funcional**: comprueba que una funcionalidad completa (endpoint + lógica + BD) produce el resultado esperado.
- **Unitario**: prueba una pieza de lógica aislada (en este caso, el validador de contraseña de Pydantic).
- **Seguridad**: verifica que el control de acceso funciona correctamente (rutas protegidas).

La técnica de **caja negra** se aplica cuando el test solo mira la entrada y la salida (código de respuesta, estructura JSON) sin importar cómo está implementado internamente. La técnica de **caja blanca** se aplica cuando el test conoce la lógica interna y diseña los casos en función de ella (filtros, paginación, validaciones específicas).
