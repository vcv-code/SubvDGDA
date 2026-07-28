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
        reset-db dataset cargar test logs logs-cron logs-nginx \
        backup restore shell-db mailpit uninstall

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
# CUIDADO: esto NO se recupera solo del dataset. Se pierde todo lo que vive
# únicamente en la BD y no está en data/final/:
#   · convocatorias que descubrió el cron consultando BDNS (las del año en
#     curso, posteriores al último año del dataset),
#   · las fecha_fin_plazo fijadas a mano desde el panel admin,
#   · los usuarios (salvo el admin que siembra docker/init/modelo-fisico.sql).
# Haz `make backup` antes y comprueba los avisos después.
#
# No hace falta esperar a la BD a mano: `up -d` ya bloquea hasta que el
# healthcheck de `db` pasa, porque backend/cron/adminer dependen de
# `condition: service_healthy`.
reset-db:
	@echo "⚠️  Esto borrará todos los datos. ¿Continuar? [s/N]" && read ans && [ "$$ans" = "s" ]
	cd docker && docker compose down -v && docker compose up -d
	venv/bin/python -m scripts.data_processing.cargar_dataset

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
	venv/bin/python -m scripts.data_processing.cargar_dataset

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

backup:
	docker exec bdns_dgda_db mariadb-dump -ubdns_user -pbdns_pass bdns_dgda \
		> backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup guardado en el directorio actual."

restore:
	@test -n "$(FILE)" || (echo "Uso: make restore FILE=backup_YYYYMMDD_HHMMSS.sql"; exit 1)
	docker exec -i bdns_dgda_db mariadb -ubdns_user -pbdns_pass bdns_dgda < $(FILE)
	@echo "Backup $(FILE) restaurado."

shell-db:
	docker exec -it bdns_dgda_db mariadb -ubdns_user -pbdns_pass bdns_dgda

mailpit:
	@echo "Mailpit disponible en http://localhost:8025"
	@which xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8025 || \
	 which open       >/dev/null 2>&1 && open       http://localhost:8025 || \
	 echo "(Ábrelo manualmente en el navegador)"

uninstall:
	bash uninstall.sh
