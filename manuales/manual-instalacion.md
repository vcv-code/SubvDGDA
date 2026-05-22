# Manual de instalación y configuración

## Plataforma de análisis de subvenciones de bienestar animal

**Versión:** 1.0 — Mayo 2026

---

## Requisitos previos

Antes de instalar la aplicación, asegúrate de tener instaladas las siguientes herramientas en tu sistema:

| Herramienta | Versión mínima | Para qué se usa |
|-------------|---------------|-----------------|
| **Docker** con `docker compose` v2 | Docker 24+ | Orquestación de todos los servicios |
| **Python** | 3.10+ | Entorno virtual para scripts de datos y tests* |
| **openssl** | Cualquier versión reciente | Generación del certificado SSL |

*No es imprescindible para el funcionamiento de la aplicación.

**Plataformas compatibles:** Linux, macOS, Windows con WSL2 y Docker Desktop.

### Verificar los requisitos

```bash
docker --version          # Docker version 24.x.x o superior
docker compose version    # Docker Compose version v2.x.x
python3 --version         # Python 3.10 o superior
openssl version           # OpenSSL 1.x o superior
```

### Espacio en disco necesario

- ~400 MB para las imágenes Docker (primera descarga)
- ~50 MB para el entorno virtual Python (opcional, solo para tests y scripts)
- ~10 MB para el dataset de subvenciones

---

## Instalación automática (recomendada)

### Paso 1 — Clonar el repositorio

```bash
git clone git@github.com:vcv-code/analisis-bdns-dgda.git
cd analisis-bdns-dgda
```

### Paso 2 — Ejecutar el script de instalación

```bash
bash install.sh
```

El script guía el proceso paso a paso con explicaciones en lenguaje llano. Hace tres preguntas:

**Pregunta 1 — Confirmación inicial**

```
¿Continuar? [s/N]:
```

Escribe `s` para continuar. Si pulsas Enter sin escribir nada, el script se cancela sin modificar nada en tu sistema.

**Pregunta 2 — Dominio local (opcional pero recomendado)**

```
¿Añadir subvencionesDGDA.local a /etc/hosts? [s/N]:
```

- Si escribes `s`: la app estará disponible en `https://subvencionesDGDA.local` con HTTPS completo. Esta opción requiere contraseña de administrador (`sudo`).
- Si pulsas Enter: la app estará disponible en `http://localhost` sin HTTPS. Algunas funcionalidades relacionadas con las cookies seguras pueden no funcionar correctamente en esta modalidad.

**Pregunta 3 — Entorno virtual Python (opcional)**

```
¿Crear entorno virtual Python (venv)? (solo para tests y scripts) [s/N]:
```

- Si escribes `s`: se crea el entorno virtual (~50 MB) necesario para ejecutar los tests automáticos y los scripts de procesamiento de datos.
- Si pulsas Enter: no se crea. **La aplicación web funciona igualmente sin el venv.** Solo es necesario si quieres ejecutar `make test` o los parsers de datos manualmente.

### Paso 3 — Esperar a que termine

El script descarga las imágenes Docker (solo la primera vez, ~400 MB), construye la imagen del backend, levanta los servicios y carga el dataset completo. El proceso completo tarda entre 5 y 15 minutos en una primera instalación, dependiendo de la velocidad de conexión.

Al terminar, el script muestra la URL de acceso y las credenciales del usuario administrador de demo.

### Paso 4 — Acceder a la aplicación

Abre el navegador y ve a:

- `https://subvencionesDGDA.local` (si añadiste el dominio)
- `http://localhost` (alternativa)

Si el navegador muestra un aviso de certificado no seguro, haz clic en **Avanzado → Continuar a subvencionesDGDA.local**. Es normal: el certificado es autofirmado para el entorno local.

### Credenciales de demo

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | `admin@demo.com` | `Admin1234!` |
| Usuario registrado | `usuario@demo.com` | `User1234!` |

---

## Verificación de la instalación

Comprueba que todos los servicios están en marcha:

```bash
cd docker
docker compose ps
```

Deberías ver seis contenedores en estado `running` o `healthy`:

| Contenedor | Estado esperado |
|------------|----------------|
| bdns_dgda_db | healthy |
| bdns_api | running |
| bdns_nginx | running |
| bdns_cron | running |
| bdns_mailpit | running |
| bdns_adminer | running |

Verifica también que los datos se han cargado correctamente:

```bash
docker exec bdns_dgda_db mariadb -uroot -proot bdns_dgda \
  -e "SELECT COUNT(*) AS solicitudes FROM solicitudes;"
```

El resultado debería ser **6398**.

---

## Servicios disponibles con Docker levantado

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Aplicación web | `https://subvencionesDGDA.local` | Interfaz principal |
| Adminer (gestor BD) | `http://localhost:8080` | Explorador de base de datos |
| Mailpit (emails) | `http://localhost:8025` | Bandeja de emails de desarrollo |
| API (Swagger UI) | `https://subvencionesDGDA.local/docs` | Documentación interactiva de la API |

**Acceso a Adminer:** Sistema → MySQL · Servidor → `db` · usuario y contraseña según el archivo `docker/.env`.

**Mailpit:** captura todos los emails que la aplicación intenta enviar (verificación de cuenta, recuperación de contraseña) sin que lleguen a ningún destinatario real.

---

## Uso diario

### Arrancar el sistema

```bash
make start
# o equivalente:
cd docker && docker compose up -d
```

### Parar el sistema (conservando los datos)

```bash
make stop
# o equivalente:
cd docker && docker compose down
```

### Ver logs

```bash
make logs          # Últimas 100 líneas del backend
make logs-cron     # Últimas 50 líneas del scheduler
make logs-nginx    # Últimas 50 líneas de Nginx
```

### Referencia completa de comandos

| Comando | Descripción |
|---------|-------------|
| `make start` | Levanta todos los contenedores |
| `make stop` | Para los contenedores (conserva los datos) |
| `make restart` | Para y vuelve a levantar |
| `make build` | Reconstruye la imagen del backend |
| `make reload-nginx` | Recarga la configuración de Nginx sin reiniciar |
| `make reset-db` | Borra el volumen y recarga el dataset (pide confirmación) |
| `make test` | Ejecuta los tests automáticos con pytest |
| `make backup` | Genera un backup de la BD en SQL |
| `make shell-db` | Abre la consola MariaDB dentro del contenedor |
| `make mailpit` | Muestra la URL de Mailpit |
| `make uninstall` | Ejecuta el script de desinstalación |

---

## Actualizar el proyecto

Cuando haya cambios en el repositorio:

```bash
git pull
bash install.sh   # responde 's' para continuar
```

El script detecta la instalación existente, aplica las migraciones del esquema si las hay y reconstruye el backend. Los datos no se tocan.

---

## Modo desarrollo (opcional)

Para desarrollar en el backend sin reconstruir la imagen en cada cambio, puedes arrancar solo la base de datos en Docker y ejecutar el servidor localmente:

```bash
# Terminal 1 — solo la BD en Docker
cd docker
docker compose up -d db

# Terminal 2 — backend con recarga automática
source venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
```

La documentación de la API estará disponible en `http://localhost:8000/docs`.

---

## Instalación en Windows con WSL2

Si usas Windows, el entorno recomendado es WSL2 con Docker Desktop:

1. Instala Docker Desktop para Windows con la integración WSL2 activada.
2. Abre una terminal WSL2 (Ubuntu u otra distribución Linux).
3. Navega a la carpeta del proyecto dentro del sistema de archivos de Linux (no desde `/mnt/c/...`).
4. Sigue los pasos de instalación normales con `bash install.sh`.

**Nota sobre el dominio en Windows:** Si añades `subvencionesDGDA.local` al `/etc/hosts` de WSL2, también tendrás que añadirlo al archivo `hosts` de Windows para acceder desde el navegador de Windows:

```
C:\Windows\System32\drivers\etc\hosts
```

Añade la línea: `127.0.0.1 subvencionesDGDA.local`

Este archivo requiere abrirlo como administrador para poder editarlo.

**Solución a problemas con bind mounts en WSL2:** Si algún contenedor falla al arrancar con errores relacionados con volúmenes o archivos, ejecuta:

```bash
cd docker
docker compose down
docker compose up -d
```

---

## Ejecutar los tests

El entorno virtual Python es necesario para ejecutar los tests:

```bash
# Si no existe el venv, crearlo primero:
python3 -m venv venv
source venv/bin/activate
pip install -r requeriments.txt

# Ejecutar todos los tests:
make test
# o:
source venv/bin/activate && pytest tests/ -q
```

**Resultado esperado:**

- Sin Docker: `181 passed`
- Con Docker y Nginx levantados: `197 passed`

---

## Desinstalación

Para eliminar completamente el entorno de la plataforma:

```bash
bash uninstall.sh
```

El script pregunta antes de cada operación irreversible y explica en lenguaje sencillo qué elimina en cada paso:

1. Contenedores y volúmenes Docker (incluye todos los datos de la BD)
2. Imagen Docker del backend (libera ~75 MB, opcional)
3. Entrada en `/etc/hosts` (requiere `sudo`, opcional)
4. Archivos generados: `docker/.env`, certificado SSL
5. Entorno virtual `venv/` (libera ~50 MB, opcional)

Una vez completada la desinstalación, puedes eliminar la carpeta del proyecto si lo deseas:

```bash
cd ..
rm -rf analisis-bdns-dgda
```

Para reinstalar desde cero: `bash install.sh`.

---

## Resolución de problemas comunes

**El navegador muestra "Esta web no es segura" y no deja continuar**

El certificado es autofirmado y el navegador lo marca como no confiable. Busca la opción "Avanzado" o "Más información" y haz clic en "Continuar a subvencionesDGDA.local de todos modos".

**El contenedor `bdns_nginx` no arranca**

Comprueba que no hay otro servicio usando los puertos 80 o 443. Si reiniciaste Docker Desktop, ejecuta `make restart` para recrear los contenedores.

**La página carga pero las gráficas no aparecen**

Asegúrate de que el backend está en marcha (`docker compose ps`). Si el backend tardó en arrancar, recarga la página. Comprueba los logs con `make logs`.

**No recibo el email de verificación**

Accede a Mailpit en `http://localhost:8025`. Todos los emails enviados por la aplicación aparecen ahí, no llegan a ningún correo real.

**Los tests fallan con errores de base de datos**

Los tests usan SQLite en memoria y no requieren Docker. Si fallan, asegúrate de que el entorno virtual está activado y las dependencias están instaladas con `pip install -r requeriments.txt`.
