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
        reset-db cargar test logs logs-cron logs-nginx \
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

reset-db:
	@echo "⚠️  Esto borrará todos los datos. ¿Continuar? [s/N]" && read ans && [ "$$ans" = "s" ]
	cd docker && docker compose down -v && docker compose up -d
	@echo "Esperando a que la BD esté lista..."
	@until docker exec bdns_dgda_db mariadb -uroot -proot -e "SELECT 1" >/dev/null 2>&1; do \
		printf "."; sleep 2; \
	done && echo ""
	venv/bin/python -m scripts.data_processing.cargar_dataset

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
