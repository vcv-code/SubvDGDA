# Makefile — Subvenciones Bienestar Animal (BDNS / DGDA)
# Atajos para las tareas habituales del proyecto.
# Requiere: make, Docker, Python 3 con venv activable en venv/
#
# Windows: make no está disponible de serie.
# Opciones: (1) usar WSL2 y ejecutar desde Linux,
#           (2) instalar make con: winget install GnuWin32.Make
#           (3) copiar el comando directamente de cada target.

.PHONY: start stop restart build build-cron reload-nginx \
        mantenimiento-on mantenimiento-off \
        reset-db redescubrir-convocatorias crear-admin dataset cargar \
        test logs logs-cron logs-nginx \
        backup restore shell-db mailpit uninstall

# Los volcados de BD van a un directorio propio, ignorado por git: contienen
# datos reales (usuarios, hashes de contraseña) y no deben acabar en el repo.
BACKUP_DIR = backups

# Las credenciales de la base de datos viven en docker/.env, NO escritas aquí:
# este fichero está versionado y en un despliegue real la contraseña es
# aleatoria. Cada receta que toca la BD carga ese fichero en su propio shell
# (make ejecuta cada línea en uno distinto, así que no basta con hacerlo una vez).
# La comprobación va ANTES del `.`: make usa /bin/sh (dash), donde un `.` sobre
# un fichero inexistente mata el shell en el acto y nunca llegaría a un `||`.
ENV_BD = [ -f docker/.env ] || { echo "Falta docker/.env — ejecuta 'bash install.sh'"; exit 1; }; set -a; . docker/.env; set +a;

# ── Docker ────────────────────────────────────────────────────────────────────

start:
	cd docker && docker compose up -d

stop:
	cd docker && docker compose down

restart:
	cd docker && docker compose down && docker compose up -d

build:
	cd docker && docker compose up --build -d backend

build-cron:
	cd docker && docker compose up --build -d cron

reload-nginx:
	docker exec bdns_nginx nginx -s reload

# Modo mantenimiento: crea/borra el fichero-bandera que Nginx comprueba en cada
# petición (no necesita reload). Con la bandera presente, la web responde 503 con
# mantenimiento.html. Útil para despliegues, migraciones de BD o recargas de datos.
mantenimiento-on:
	touch frontend/maintenance.on
	@echo "Modo mantenimiento ACTIVADO — la web responde 503 con mantenimiento.html"

mantenimiento-off:
	rm -f frontend/maintenance.on
	@echo "Modo mantenimiento DESACTIVADO — la web vuelve a estar disponible"

# ── Base de datos ─────────────────────────────────────────────────────────────

# Recrea la BD desde cero. Hace falta cada vez que cambia el dataset: el
# cargador solo INSERTA (ver `cargar`), así que sobre la BD existente no
# borraría los registros que ya no están ni actualizaría los que cambiaron.
#
# CUIDADO: el dataset no lo recupera todo. Vive solo en la BD, y no en
# data/final/, lo siguiente:
#   · convocatorias que descubrió el cron consultando BDNS (las del año en
#     curso, posteriores al último año del dataset),
#   · las fecha_fin_plazo fijadas a mano desde el panel admin,
#   · los usuarios (salvo el admin que siembra docker/init/modelo-fisico.sql).
# Por eso el target hace un backup automático antes de borrar (paso 1) y
# vuelve a lanzar el cron al final (paso 4). Aun así, revisa los avisos
# cuando termine: el cron repone las convocatorias, pero NO las
# fecha_fin_plazo, que son dato propio y no de BDNS — esas salen del backup.
#
# No hace falta esperar a la BD a mano: `up -d` ya bloquea hasta que el
# healthcheck de `db` pasa, porque backend/cron/adminer dependen de
# `condition: service_healthy`.
reset-db:
	@docker ps --format '{{.Names}}' | grep -qx bdns_dgda_db || \
		(echo "La BD no está levantada, así que no se puede hacer el backup previo."; \
		 echo "Arranca con 'make start' y vuelve a intentarlo."; exit 1)
	@echo "⚠️  Esto borrará todos los datos. ¿Continuar? [s/N]" && read ans && [ "$$ans" = "s" ]
	@$(MAKE) --no-print-directory backup
	cd docker && docker compose down -v && docker compose up -d
	@$(ENV_BD) venv/bin/python -m scripts.data_processing.cargar_dataset
	@$(MAKE) --no-print-directory redescubrir-convocatorias
	@$(MAKE) --no-print-directory crear-admin
	@echo ""
	@echo "Comprueba los avisos:  curl -sk https://localhost/avisos/"
	@echo "Si faltan fecha_fin_plazo, están en el backup de $(BACKUP_DIR)/."
	@echo "Procedimiento: manuales/manual-instalacion.md > Resolución de problemas comunes"

# Vuelve a lanzar el cron para redescubrir las convocatorias del año en curso.
#
# El borrado del fichero de estado NO es opcional. check_bdns.py guarda en
# logs/cron/estado_<año>.json qué convocatorias ya registró, y si constan las
# dos (eell y epa) se salta la búsqueda entera y solo comprueba resoluciones.
# Ese fichero es un espejo de la BD: si se borra una y no el otro, quedan
# desincronizados y el cron no repondría nada.
#
# No corta el target si falla: necesita red y que BDNS responda, y una BD
# recién cargada es utilizable aunque falten las convocatorias del año.
redescubrir-convocatorias:
	@rm -f logs/cron/estado_*.json
	@docker exec bdns_cron python3 /app/scripts/check_bdns.py \
		|| echo "AVISO: el cron no pudo completarse (¿sin red o BDNS caído?). Las convocatorias del año en curso pueden faltar."

# Crea la cuenta de administración preguntando la contraseña. Ni el esquema ni
# install.sh siembran usuarios con contraseña escrita: un hash válido dentro
# del repositorio sería la contraseña de administración de todo despliegue
# nuevo. reset-db lo invoca al final para no dejarte sin ninguna cuenta.
# No hace nada si ya existe un admin.
crear-admin:
	@bash scripts/crear_admin.sh

# Regenera data/final/dataset_unificado.json desde los JSON procesados.
# El segundo paso NO es opcional: unificar_datasets.py reescribe el fichero
# con las causas de exclusión tal cual vienen del BOE ("10, 12, 16"), y
# normalizar_causa_exclusion.py las deja en su forma canónica ("10;12;16").
# Ejecutar solo el primero revierte la normalización de ~370 registros.
dataset:
	venv/bin/python scripts/data_processing/unificar_datasets.py
	venv/bin/python scripts/data_processing/normalizar_causa_exclusion.py
	@echo "Dataset regenerado. Para llevarlo a la BD: make reset-db (no basta con make cargar)."

# Carga aditiva: inserta lo que falta y salta lo que ya existe por
# (num_expediente, id_convoc). Nunca actualiza ni borra — sirve para poblar
# una BD vacía o añadir una convocatoria nueva, no para reflejar cambios en
# registros ya cargados. Para eso, make reset-db.
cargar:
	@$(ENV_BD) venv/bin/python -m scripts.data_processing.cargar_dataset

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	venv/bin/python -m pytest tests/ -q

test-v:
	venv/bin/python -m pytest tests/ -v

# ── Logs ──────────────────────────────────────────────────────────────────────

logs:
	docker logs bdns_api --tail 100

logs-cron:
	docker logs bdns_cron --tail 50

logs-nginx:
	docker logs bdns_nginx --tail 50

# ── Utilidades ────────────────────────────────────────────────────────────────

# El fichero se borra si el volcado falla: la redirección lo crea antes de que
# mariadb-dump escriba nada, así que un fallo dejaría un .sql de 0 bytes con
# pinta de backup bueno — justo lo que no quieres encontrarte al restaurar.
backup:
	@mkdir -p $(BACKUP_DIR)
	@F=$(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql; \
	if $(ENV_BD) docker exec bdns_dgda_db mariadb-dump \
		-u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE" > $$F; then \
		echo "Backup guardado en $$F"; \
	else \
		rm -f $$F; \
		echo "ERROR: no se pudo volcar la BD (¿está levantada? prueba make start)."; \
		exit 1; \
	fi

restore:
	@test -n "$(FILE)" || (echo "Uso: make restore FILE=backups/backup_YYYYMMDD_HHMMSS.sql"; exit 1)
	@$(ENV_BD) docker exec -i bdns_dgda_db mariadb \
		-u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE" < $(FILE)
	@echo "Backup $(FILE) restaurado."

shell-db:
	@$(ENV_BD) docker exec -it bdns_dgda_db mariadb \
		-u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE"

mailpit:
	@echo "Mailpit disponible en http://localhost:8025"
	@which xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8025 || \
	 which open       >/dev/null 2>&1 && open       http://localhost:8025 || \
	 echo "(Ábrelo manualmente en el navegador)"

uninstall:
	bash uninstall.sh
