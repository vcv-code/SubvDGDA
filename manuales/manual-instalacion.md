# Manual de instalación y configuración

## Plataforma de análisis de subvenciones de bienestar animal

**Versión:** 1.0 — Mayo 2026

---

## Comandos rápidos (TL;DR)

> Esta sección asume **Windows con WSL2** (entorno habitual del proyecto). Si usas Linux o macOS, omite `wsl` y `code .` — el resto de comandos funcionan igual. Los prerrequisitos universales (Docker, Python, openssl) están en la sección [Requisitos previos](#requisitos-previos).

Si ya tienes los prerrequisitos preparados (en Windows: WSL2 + Docker Desktop + VS Code; en Linux/macOS: Docker + Python con `venv`) y el proyecto en `~/analisis-bdns-dgda-main/`:

### Instalar

```bash
wsl
cd ~/analisis-bdns-dgda-main
code .
bash install.sh
```

### Primera vez en este sistema (Ubuntu/Debian sin `venv`)

```bash
sudo apt install python3.12-venv   # sustituye 3.12 por tu versión
bash install.sh
```

### Guardar BD antes de reinstalar

```bash
docker exec bdns_dgda_db mariadb-dump -ubdns_user -pbdns_pass bdns_dgda > /tmp/backup.sql
# o con make:
make backup
```

### Restaurar BD tras reinstalar

```bash
docker exec -i bdns_dgda_db mariadb -ubdns_user -pbdns_pass bdns_dgda < /tmp/backup.sql
# o con make:
make restore FILE=backup_20260525_120000.sql
```

### Desinstalar

```bash
bash uninstall.sh
```

> **Nota sobre el arranque de la BD:** en primera instalación con WSL2 lento, MariaDB puede tardar hasta 2-3 minutos en crear su `datadir`. El script espera 180 s y, si se agota, ofrece esperar 60 s más antes de abortar. En reinstalaciones suele tardar 20-30 s.

---

## Requisitos previos

Antes de instalar la aplicación, asegúrate de tener instaladas las siguientes herramientas en tu sistema:

| Herramienta | Versión mínima | Para qué se usa |
|-------------|---------------|-----------------|
| **Docker** con `docker compose` v2 | Docker 24+ | Orquestación de todos los servicios |
| **Python** | 3.10+ | Carga inicial del dataset y entorno virtual para tests/scripts |
| **python3-venv** | igual que Python | Crear el entorno virtual. En Ubuntu/Debian es un paquete aparte (p. ej. `sudo apt install python3.12-venv`) |
| **openssl** | Cualquier versión reciente | Generación del certificado SSL |

Python y `python3-venv` son necesarios en la primera instalación, porque el script crea un entorno virtual con PyMySQL para cargar el dataset en MariaDB. Una vez instalada, la aplicación web funciona en Docker sin necesidad de Python en el host.

> **Ubuntu/Debian:** el módulo `venv` de Python viene en un paquete separado. Si usas Python 3.12, instala también:
>
> ```bash
> sudo apt install python3.12-venv
> ```
>
> Si usas otra versión, sustituye `3.12` por tu versión (`python3 --version`). El script de instalación detecta si falta este paquete y te lo indica antes de continuar.

**Plataformas compatibles:** Linux, macOS, Windows con WSL2 y Docker Desktop.

### Verificar los requisitos

```bash
docker --version          # Docker version 24.x.x o superior
docker compose version    # Docker Compose version v2.x.x
python3 --version         # Python 3.10 o superior
python3 -m venv --help    # Comprueba que el módulo venv está disponible
openssl version           # OpenSSL 1.x o superior
```

### Espacio en disco necesario

**Total estimado: ~1,5 GB** (de los cuales las imágenes Docker ocupan ~1,3 GB).

Desglose:

- Backend (Docker): ~360 MB
- Cron (Docker): ~195 MB
- MariaDB (imagen oficial): ~460 MB
- Adminer: ~170 MB
- Nginx alpine: ~90 MB
- Mailpit: ~50 MB
- Dataset + datos cargados en BD: ~50 MB
- Entorno virtual Python (`venv/`): ~50 MB (opcional, solo si se ejecutan tests/scripts)

---

## Instalación automática (recomendada)

### Paso 1 — Clonar el repositorio

```bash
git clone git@github.com:vcv-code/SubvDGDA.git
cd analisis-bdns-dgda
```

### Paso 2 — Ejecutar el script de instalación

```bash
bash install.sh
```

El script guía el proceso paso a paso con explicaciones en lenguaje llano. Hace tres preguntas:

**Pregunta 1 — Confirmación inicial**

```text
¿Continuar? [s/N]:
```

Escribe `s` para continuar. Si pulsas Enter sin escribir nada, el script se cancela sin modificar nada en tu sistema.

**Pregunta 2 — Dominio local (opcional pero recomendado)**

```text
¿Añadir subvencionesDGDA.local a /etc/hosts? [s/N]:
```

- Si escribes `s`: la app estará disponible en `https://subvencionesDGDA.local` con HTTPS completo. Esta opción requiere contraseña de administrador (`sudo`).
- Si pulsas Enter: la app estará disponible en `http://localhost` sin HTTPS. Algunas funcionalidades relacionadas con las cookies seguras pueden no funcionar correctamente en esta modalidad.

**Pregunta 3 — Entorno virtual Python**

```text
¿Crear entorno virtual Python (venv)? (solo para tests y scripts) [s/N]:
```

- Si escribes `s`: se crea el entorno virtual (~50 MB) con todas las dependencias del proyecto, necesario para ejecutar los tests automáticos y los scripts de procesamiento de datos.
- Si pulsas Enter: el script no preinstala el entorno completo. **Aun así, en una primera instalación el venv se creará automáticamente más adelante**, porque la carga del dataset en MariaDB necesita PyMySQL. La diferencia es que en ese caso solo se instalan las dependencias estrictamente necesarias para la carga y no quedará listo para ejecutar `make test`.

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
| bdns_api | healthy |
| bdns_nginx | healthy |
| bdns_cron | Up (sin healthcheck) |
| bdns_mailpit | healthy |
| bdns_adminer | Up (sin healthcheck) |

Verifica también que los datos se han cargado correctamente:

```bash
docker exec bdns_dgda_db mariadb -ubdns_user -pbdns_pass bdns_dgda \
  -e "SELECT COUNT(*) AS solicitudes FROM solicitudes;"
```

El resultado debería ser **6398**.

Comprueba que las convocatorias vigentes están registradas (necesarias para los avisos de la home):

```bash
docker exec bdns_dgda_db mariadb -ubdns_user -pbdns_pass bdns_dgda \
  -e "SELECT tipo_convoc, anio_convocatoria, fecha_resolucion FROM convocatorias WHERE anio_convocatoria=2026;"
```

Deben aparecer dos filas (EPA y EELL 2026) con `fecha_resolucion` en `NULL`. Eso hace que la página de inicio muestre los dos avisos de convocatorias pendientes de resolución. Si no aparecen, vuelve a ejecutar `bash install.sh` — el script las inserta automáticamente.

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

Windows requiere WSL2 como capa de compatibilidad Linux. Sigue estos pasos en orden — saltarse alguno es la causa más frecuente de que Docker no funcione.

### Paso 0 — Software necesario

Instala todo esto antes de empezar:

| Software | Dónde obtenerlo |
|----------|----------------|
| **WSL2** | `wsl --install` en PowerShell como administrador (instala Ubuntu por defecto) |
| **Docker Desktop** | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) — versión para Windows |
| **Visual Studio Code** | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Extensión WSL** (VS Code) | Busca "WSL" en el panel de extensiones de VS Code e instálala |

### Paso 1 — Activar la integración WSL2 en Docker Desktop

Sin este paso, Docker no funciona dentro de WSL y `docker ps` dará errores.

1. Abre Docker Desktop
2. Ve a **Settings → Resources → WSL Integration**
3. Activa el interruptor de **Ubuntu**
4. Haz clic en **Apply & Restart**

Comprobación desde Ubuntu (WSL):

```bash
docker ps
```

Debe responder aunque no haya contenedores activos. Si da error, repite el paso anterior.

### Paso 2 — Establecer Ubuntu como distro WSL por defecto

Desde PowerShell (Windows):

```powershell
wsl --set-default Ubuntu
```

Esto garantiza que el comando `wsl` sin argumentos abre Ubuntu y no otra distro (como `docker-desktop`, que es interna de Docker).

### Paso 3 — Copiar el proyecto al sistema de archivos Linux

> **Regla crítica:** trabaja SIEMPRE desde el sistema de archivos Linux (`/home/...`), NUNCA desde la ruta montada de Windows (`/mnt/c/...`).

Por qué importa:

- Los bind mounts de Docker funcionan correctamente
- VS Code Remote WSL funciona sin problemas
- Sin errores de permisos en scripts
- Velocidad de I/O mucho mayor

Si tienes el proyecto descargado en Windows (por ejemplo en el Escritorio), cópialo al home de Linux desde una terminal Ubuntu:

```bash
cp -r /mnt/c/Users/TU_USUARIO/Desktop/analisis-bdns-dgda-main ~/
cd ~/analisis-bdns-dgda-main
```

> **Problema habitual — carpeta doble:** cuando descargas el ZIP desde GitHub y lo descomprimes en Windows, suele quedar una carpeta dentro de otra con el mismo nombre:
>
> ```text
> analisis-bdns-dgda-main/
> └── analisis-bdns-dgda-main/   ← aquí están los archivos reales
>     ├── install.sh
>     ├── docker/
>     └── ...
> ```
>
> Si copias la carpeta exterior, después de `cd ~/analisis-bdns-dgda-main` el `ls` no muestra `install.sh` sino otra carpeta con el mismo nombre. La solución es entrar un nivel más:
>
> ```bash
> cd ~/analisis-bdns-dgda-main/analisis-bdns-dgda-main
> ```
>
> O mejor, copiar directamente la carpeta interior:
>
> ```bash
> cp -r "/mnt/c/Users/TU_USUARIO/Desktop/analisis-bdns-dgda-main/analisis-bdns-dgda-main" ~/
> ```

Verifica que estás en la ruta correcta — `install.sh` debe ser visible:

```bash
pwd
# debe devolver: /home/TU_USUARIO/analisis-bdns-dgda-main
# NO: /mnt/c/...

ls install.sh   # debe existir; si no, estás un nivel por encima
```

### Paso 4 — Abrir VS Code desde WSL

Desde la terminal Ubuntu, dentro de la carpeta del proyecto:

```bash
code .
```

VS Code se abre en modo remoto WSL. Comprueba que en la esquina inferior izquierda aparece **WSL: Ubuntu**. Si aparece solo el nombre del proyecto sin "WSL:", no está en modo remoto — ciérralo y ábrelo de nuevo con `code .` desde la terminal Ubuntu.

### Paso 5 — Arreglar finales de línea (si el proyecto viene de Windows)

Si descargaste el ZIP desde Windows o clonaste en una máquina Windows, los archivos `.sh` pueden tener finales de línea CRLF en lugar de LF. En ese caso `bash install.sh` falla con un error críptico:

```text
bash: ./install.sh: /usr/bin/env: bad interpreter: No such file or directory
```

Instala `dos2unix` y conviértelos:

```bash
sudo apt install dos2unix -y
dos2unix install.sh uninstall.sh
```

Luego ya puedes ejecutar normalmente:

```bash
bash install.sh
```

### Paso 6 — Contraseña sudo

Cuando el script pide contraseña de administrador (para `/etc/hosts`), es la contraseña de tu **usuario Linux** (la que pusiste al instalar Ubuntu en WSL). No es la contraseña de Windows ni la de root.

Si no recuerdas cuál es o nunca la configuraste:

```bash
passwd
```

### Nota sobre el dominio en Windows

Si añades `subvencionesDGDA.local` al `/etc/hosts` de WSL2, el navegador de Windows usará su propio archivo `hosts` y no el de WSL, así que también tendrás que añadirlo en Windows. Abre **Notepad como administrador** y edita:

```text
C:\Windows\System32\drivers\etc\hosts
```

Añade al final:

```text
127.0.0.1 subvencionesDGDA.local
```

### Solución a problemas con bind mounts en WSL2

Si algún contenedor falla al arrancar con errores de volúmenes o archivos, recrear los contenedores suele solucionarlo:

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
pip install -r requeriments.txt -r backend/requirements.txt

# Ejecutar todos los tests:
make test
# o:
source venv/bin/activate && pytest tests/ -q
```

**Resultado esperado:**

- Sin Docker (excluye tests de HTTPS y rate limiting): `305 passed`
- Con Docker y Nginx levantados (suite completa): `321 passed`

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
5. Entorno virtual `venv/` (libera ~175 MB, opcional)

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

**Un contenedor se comporta raro pese a `make restart`**

Si tras un `make restart` (que hace `down && up -d`) un contenedor sigue dando problemas — no responde, no recoge una imagen recién pulleada, conexión persistente envenenada — fuerza la recreación:

```bash
cd docker
docker compose up --force-recreate -d
```

A diferencia de `up -d`, `--force-recreate` ignora si la configuración del contenedor ha cambiado y mata + crea de nuevo cada uno. Reservalo para cuando algo está claramente "atascado" — no como rutina.

**La página carga pero las gráficas no aparecen**

Asegúrate de que el backend está en marcha (`docker compose ps`). Si el backend tardó en arrancar, recarga la página. Comprueba los logs con `make logs`.

**No recibo el email de verificación**

Accede a Mailpit en `http://localhost:8025`. Todos los emails enviados por la aplicación aparecen ahí, no llegan a ningún correo real.

**Los tests fallan con errores de base de datos**

Los tests usan SQLite en memoria y no requieren Docker. Si fallan, asegúrate de que el entorno virtual está activado y las dependencias están instaladas con `pip install -r requeriments.txt -r backend/requirements.txt` — el segundo fichero contiene `pytest` y el resto de dependencias del backend.

**Error "ensurepip is not available" al crear el entorno virtual**

Ocurre en Ubuntu/Debian cuando falta el paquete `python3.X-venv`. El script de instalación lo detecta en la Fase 2 y muestra el comando exacto, pero si te ocurre manualmente:

```bash
# Consulta tu versión de Python
python3 --version   # ej. Python 3.12.x

# Instala el paquete correspondiente
sudo apt install python3.12-venv   # sustituye 3.12 por tu versión

# Vuelve a ejecutar el script de instalación
bash install.sh
```
