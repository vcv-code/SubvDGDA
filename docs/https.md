# HTTPS y dominio local

## Por qué se hizo así

El objetivo es que la aplicación sea accesible mediante HTTPS en desarrollo local, igual que en un entorno real, pero sin depender de un dominio público ni de Let's Encrypt. Es el mismo enfoque que se aplica en la asignatura de Despliegue con Apache Tomcat, adaptado al stack de este proyecto (Nginx + Docker + Python).

Nginx actúa como **terminador SSL**: recibe las peticiones HTTPS del navegador, descifra el tráfico y lo reenvía al backend (FastAPI/uvicorn) por HTTP interno. El backend no necesita saber nada de SSL.

---

## Componentes

### Dominio local

Se añade una entrada en el archivo `/etc/hosts` del sistema operativo:

```
127.0.0.1 subvencionesDGDA.local
```

En Windows: `C:\Windows\System32\drivers\etc\hosts` (requiere Bloc de notas como administrador).
En Linux/Mac: `/etc/hosts` (requiere `sudo`).

Sin este paso el navegador no sabe a qué IP apunta el dominio y no puede conectar.

### Certificado autofirmado

Se genera con `openssl` un certificado válido 1 año para `subvencionesDGDA.local`:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/server.key \
  -out docker/ssl/server.crt \
  -subj "/CN=subvencionesDGDA.local/O=DAW/C=ES" \
  -addext "subjectAltName=DNS:subvencionesDGDA.local,DNS:localhost"
```

El campo `subjectAltName` es obligatorio para que los navegadores modernos acepten el certificado (aunque sea autofirmado). Sin él, Chrome y Firefox rechazan la conexión en lugar de mostrar solo la advertencia.

Dos archivos resultantes en `docker/ssl/`:
- `server.crt` — el certificado público. Se versiona en el repositorio.
- `server.key` — la clave privada. **No se versiona** (excluida en `.gitignore`). Cada instalación tiene la suya.

### Nginx

Dos bloques `server` en `docker/nginx/default.conf`:

- **Puerto 80 (HTTP)**: solo redirige con `return 301` a HTTPS. No sirve contenido.
- **Puerto 443 (HTTPS)**: sirve la aplicación completa con el certificado. Incluye la cabecera `Strict-Transport-Security` que indica al navegador que este dominio es siempre HTTPS.

Los protocolos se limitan a TLS 1.2 y 1.3, descartando versiones antiguas e inseguras.

### Docker Compose

Nginx expone el puerto 443 además del 80, y monta la carpeta `docker/ssl/` como volumen de solo lectura:

```yaml
ports:
  - "80:80"
  - "443:443"
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

---

## Cómo reproducir el entorno (instalación nueva)

1. Generar el certificado con el comando `openssl` indicado arriba (desde la raíz del proyecto)
2. Añadir `127.0.0.1 subvencionesDGDA.local` al `/etc/hosts` del sistema
3. Levantar los contenedores: `docker compose up -d` desde `docker/`
4. Acceder a `https://subvencionesDGDA.local` — el navegador mostrará un aviso por certificado autofirmado; aceptar para continuar

Estos dos primeros pasos se incluirán en el script de instalación automática cuando esté disponible.

---

## Diferencia con producción

En producción con un dominio real, el certificado autofirmado se sustituye por uno de Let's Encrypt (gratuito, renovación automática, confiado por todos los navegadores sin avisos). La configuración de Nginx sería prácticamente la misma — solo cambiaría la ruta del certificado.
