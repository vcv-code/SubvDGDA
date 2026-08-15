# Manual de despliegue en un servidor

Cómo se puso este proyecto en internet, paso a paso y con el porqué de cada
decisión. Escrito sobre el despliegue real del **15 de agosto de 2026** en un
VPS de Contabo con Ubuntu 24.04.

Para instalarlo en tu propio ordenador, el documento es otro:
[manual-instalacion.md](manual-instalacion.md).

---

## Índice

1. [Antes de empezar](#antes-de-empezar)
2. [Fase 1 — Asegurar el servidor](#fase-1--asegurar-el-servidor)
3. [Fase 2 — Docker](#fase-2--docker)
4. [Fase 3 — Dominio y DNS](#fase-3--dominio-y-dns)
5. [Fase 4 — Desplegar la aplicación](#fase-4--desplegar-la-aplicación)
6. [Fase 5 — HTTPS con Let's Encrypt](#fase-5--https-con-lets-encrypt)
7. [Fase 6 — Comprobar desde fuera](#fase-6--comprobar-desde-fuera)
8. [Fase 7 — Snapshot](#fase-7--snapshot)
9. [Reconciliar un servidor desplegado antes de esta separación](#reconciliar-un-servidor-desplegado-antes-de-esta-separación)
10. [Mantenimiento](#mantenimiento)
11. [Errores que nos encontramos](#errores-que-nos-encontramos)

---

## Antes de empezar

**El orden importa y no es negociable: se asegura el servidor ANTES de subir
nada.** Desde el minuto en que la máquina existe hay bots probando contraseñas
en el puerto 22. No es alarmismo, es lo que le pasa a cualquier IP pública.
Desplegar primero y proteger después es el orden que da disgustos.

Lo que hace falta tener decidido:

| Cosa | Elegido aquí | Por qué |
|---|---|---|
| Servidor | Contabo Cloud VPS 4 (4 vCPU, 8 GB, 100 GB), 12 meses | Barato y sobrado; 12 meses en vez de 24 para no atarse a un proveedor sin probarlo |
| Ubicación | Unión Europea | RGPD y coherencia con la política de privacidad |
| Sistema | Ubuntu 24.04 LTS | Es lo que el proyecto usa y prueba |
| Dominio | Cloudflare Registrar | Vende a precio de coste, sin subidas en la renovación, con privacidad WHOIS gratis |
| Correo | Gmail con contraseña de aplicación | Volumen bajísimo y cuenta ya existente |

### Generar contraseñas seguras

Vas a necesitar varias a lo largo del proceso. Dos comandos, según para qué:

```bash
openssl rand -hex 24      # 48 caracteres, solo 0-9 y a-f
openssl rand -base64 24   # 32 caracteres, con mayúsculas, minúsculas y símbolos
```

**Cuál usar:**

- **`-hex`** para lo que va a leer un programa: `docker/.env`, cadenas de
  conexión, claves de firma. No lleva símbolos, así que nada tiene que
  escaparse ni se rompe al pasar por un fichero de configuración.
- **`-base64`** para lo que vas a teclear tú en un formulario web: el panel del
  proveedor, el registrador de dominios. Más fuerte por carácter.

**Dónde ejecutarlo — la regla es: genérala donde se va a usar, para que no
viaje.**

| Para qué | Dónde generarla |
|---|---|
| Contraseña `root` del servidor, al contratarlo | Tu ordenador (todavía no hay servidor) |
| Secretos de `docker/.env` | **En el servidor**, así no salen de ahí ni un momento |
| Paneles del proveedor y del registrador | Tu ordenador |

Y en todos los casos: **cópiala a tu gestor de contraseñas antes de pegarla en
ningún sitio.** Algunas no se pueden recuperar — la de `root` del servidor, si la
pierdes, obliga a reinstalar la máquina.

Un aviso que parece obvio y no lo es: **no hagas capturas de pantalla con
contraseñas, secretos de doble factor o códigos de recuperación visibles.** Es
la forma más habitual de que una credencial acabe donde no debe.

### Qué se comparó antes de elegir

> Los precios son de **agosto de 2026** y envejecen rápido. Lo que sigue siendo
> útil es el criterio, no la cifra.

**Servidor.** Se miraron cuatro:

| Proveedor | Qué ofrecía | Por qué se descartó o eligió |
|---|---|---|
| **Hetzner** | Su gama barata (~7 €) es la mejor relación calidad-precio del mercado | **Agotada por completo** en todas las ubicaciones. Lo que quedaba disponible costaba el triple por la misma RAM |
| **Netcup** | 4 GB por ~6 €, facturable por horas | Buena opción. Su línea «Lite» sale más barata pero ata a 6 meses pagados por adelantado |
| **IONOS** | Española, soporte en español | El «1 €» era promoción de 3 meses y los precios de la web no llevaban IVA. Solo 2 GB en ese plan |
| **Contabo** ✅ | 8 GB y 4 núcleos por ~5,66 € con IVA | **Elegido**: web y facturación en español, y el hardware más holgado por el precio. Tiene fama de disco más lento, irrelevante para una web de tráfico bajo |

Los criterios que de verdad decidieron: **precio con IVA incluido** (no el de
portada), **permanencia** —12 meses en vez de 24, para no atarse a un proveedor
sin haberlo probado—, **ubicación en la UE** y **poder entenderse con el
proveedor**.

Dos detalles que no se ven en la portada: el panel de Contabo está en español,
pero **el antiguo no** —hay que pasarse al nuevo, que además es donde están los
snapshots—, y el precio anual se cobra **entero por adelantado**.

**Dominio.** Se compararon dos:

| Registrador | Primer año | Renovación | Nota |
|---|---|---|---|
| **Cloudflare** ✅ | ~7,80 € | **~10,30 €** | Vende a precio de coste por política, no como promoción: la renovación no sube. Privacidad WHOIS gratis. **No admite dominios `.es`** |
| DonDominio | 9,35 € | **14,45 €** | Español y admite `.es`. Comprobar si el precio lleva IVA |

**Mira el precio de renovación, no el del primer año**: ahí está la trampa
habitual, y un dominio se paga una vez al año durante muchos.

Y algo que sorprende: al registrar un dominio, tus datos personales pueden
acabar en una base de datos pública consultable por cualquiera. **Comprueba que
la privacidad WHOIS esté activada** antes de pagar, no después.

---

## Fase 1 — Asegurar el servidor

### 1.1 Primera conexión y actualización

```bash
ssh root@LA.IP.DEL.SERVIDOR
apt update && apt upgrade -y
```

La primera vez pregunta si aceptas la identidad del servidor: se responde
`yes`. La contraseña no se ve al escribirla, ni asteriscos ni nada.

### 1.2 Tu clave SSH

Desde **tu ordenador**, no desde el servidor:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@LA.IP.DEL.SERVIDOR
```

**Indica la clave con `-i` explícitamente.** Sin eso, `ssh-copy-id` elige por su
cuenta y puede instalar otra que tengas por ahí — nos pasó, y acabó con una
clave ajena autorizada en el servidor.

Conviene además un `~/.ssh/config` en tu equipo:

```
Host servidor
    HostName LA.IP.DEL.SERVIDOR
    User root
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

`IdentitiesOnly yes` es lo que impide que SSH vaya ofreciendo todas las claves
que encuentre. A partir de aquí basta con `ssh servidor`.

### 1.3 Desactivar el acceso por contraseña

**Antes de nada, comprueba que la clave funciona**, y hazlo de forma que no
admita dudas:

```bash
ssh -o PreferredAuthentications=publickey servidor
```

Eso prohíbe usar contraseña. Si entras, la clave sirve. **No sigas si esto
falla**: quedarte fuera del servidor empieza justo aquí.

Ahora mira cómo está repartida la configuración:

```bash
ls /etc/ssh/sshd_config.d/
grep -rn "PasswordAuthentication\|PermitRootLogin" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/
```

**El nombre del fichero es lo más importante de este paso.** La configuración de
SSH está partida en varios ficheros y **gana la PRIMERA aparición de cada
opción, no la última**. Los proveedores suelen dejar un `50-cloud-init.conf`
con `PasswordAuthentication yes`, así que el nuestro tiene que ordenarse antes:

```bash
cat > /etc/ssh/sshd_config.d/00-hardening.conf <<'EOF'
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
EOF
```

Comprueba la configuración **ya combinada**, que es la que manda:

```bash
sshd -t && sshd -T | grep -E "^(permitrootlogin|passwordauthentication)"
```

Debe decir `passwordauthentication no`. Si dice `yes`, el fichero no está
ganando y **no hay que seguir**. (`permitrootlogin` aparecerá como
`without-password`, que es el nombre antiguo de `prohibit-password` — es lo
mismo.)

```bash
systemctl restart ssh
```

**No cierres la sesión.** SSH no corta las conexiones abiertas, así que esa
sesión sigue siendo tu red de seguridad. Comprueba desde **otra pestaña**:

```bash
ssh servidor                                              # debe entrar
ssh -o PreferredAuthentications=password root@LA.IP       # debe dar "Permission denied"
```

### 1.4 Cortafuegos

**Primero permitir SSH, después activar.** Al revés te cierra la puerta por la
que estás entrando.

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable          # responde 'y'
ufw status verbose  # solo 22, 80 y 443
```

> **AVISO IMPORTANTE: ufw no protege los puertos de Docker.**
> Docker escribe sus reglas de red *por delante* de las de ufw, así que un
> contenedor con `-p 8080:8080` queda accesible desde internet aunque el
> cortafuegos deniegue ese puerto. La protección de verdad es atar los puertos
> a `127.0.0.1` en `docker-compose.yml`, cosa que este proyecto ya hace.

**Muchos proveedores ofrecen además un cortafuegos propio** (Contabo lo incluye
gratis en su panel). Ese sí está **fuera de la máquina**, así que Docker no
puede saltárselo: es una segunda capa justo donde ufw tiene su punto flaco.

No es imprescindible si los puertos ya están atados a `127.0.0.1` —esa es la
protección buena— y mal configurado te deja fuera del servidor. Pero como red de
seguridad adicional, en un día tranquilo, merece la pena.

### 1.5 fail2ban

```bash
apt install -y fail2ban

cat > /etc/fail2ban/jail.d/00-sshd.local <<'EOF'
[sshd]
enabled  = true
backend  = systemd
maxretry = 5
bantime  = 1h
EOF

systemctl restart fail2ban
sleep 3 && fail2ban-client status sshd
```

El `backend = systemd` hace falta en Ubuntu 24.04, donde ya no existe el
fichero de log clásico que fail2ban busca por defecto.

**Su valor aquí es bajo**, todo sea dicho: sin contraseñas que adivinar, los
bots rebotan solos. Queda por si algún día hay otro servicio que proteger.

### 1.6 Reiniciar

```bash
reboot
```

Espera un minuto y vuelve con `ssh servidor`. Es buen momento porque todavía no
hay nada que se pueda estropear, y de paso confirmas que el servidor arranca
solo y te deja entrar sin ayuda.

---

## Fase 2 — Docker

```bash
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

docker --version && docker compose version && docker run --rm hello-world
```

**Usa el repositorio oficial de Docker, no el `docker.io` de Ubuntu.** Ese trae
el `docker-compose` antiguo (con guion), y este proyecto usa `docker compose`
(con espacio), que es un complemento distinto. Con el paquete de Ubuntu, ni el
`Makefile` ni `install.sh` funcionan.

---

## Fase 3 — Dominio y DNS

Cómpralo **unos días antes** del despliegue, no el mismo día: los cambios de
DNS tardan horas en extenderse y Let's Encrypt no emite el certificado hasta
que el dominio apunte al servidor.

Dos registros, apuntando a la IP:

| Tipo | Nombre | Contenido | Proxy |
|---|---|---|---|
| A | `@` | la IP del servidor | **DNS only** |
| A | `www` | la IP del servidor | **DNS only** |

> **En Cloudflare, la nube en GRIS («DNS only»), no naranja.**
> Con el proxy activado todo el tráfico pasa por Cloudflare y los registros de
> Nginx anotan **IPs de Cloudflare en lugar de las de los visitantes**, lo que
> inutiliza cualquier analítica basada en esos logs. Además obligaría a
> declarar a Cloudflare como intermediario en la política de privacidad.

Comprueba desde otra máquina que ya resuelve:

```bash
dig +short A tu-dominio.org
```

Si responde `NXDOMAIN`, el registro del dominio todavía no lo ha publicado.
Es normal recién comprado: espera y vuelve a probar.

---

## Fase 4 — Desplegar la aplicación

### 4.1 Clave de despliegue (si el repositorio es privado)

**En el servidor:**

```bash
apt install -y git
ssh-keygen -t ed25519 -C "deploy-vps" -f /root/.ssh/id_deploy -N ""
cat /root/.ssh/id_deploy.pub
```

Sin passphrase (`-N ""`) a propósito: la usa el servidor solo, sin nadie
delante, en cada `git pull`.

Esa clave **pública** se añade en GitHub → repositorio → *Settings* → *Deploy
keys* → *Add deploy key*. **Sin marcar «Allow write access»**: el servidor solo
tiene que leer.

Una clave de despliegue está atada a **un solo repositorio** y puede ser de solo
lectura. Con tu clave personal, quien entrase en el servidor tendría acceso a
toda tu cuenta de GitHub.

Luego, en el servidor:

```bash
cat > /root/.ssh/config <<'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/id_deploy
    IdentitiesOnly yes
EOF
chmod 600 /root/.ssh/config

ssh -T git@github.com    # "You've successfully authenticated" — el aviso de
                         # "does not provide shell access" es lo esperado
```

### 4.2 Clonar

```bash
git clone git@github.com:USUARIO/REPOSITORIO.git /opt/subvdgda
cd /opt/subvdgda
git log --oneline -1 && git describe --tags
```

`/opt/` es el sitio estándar para aplicaciones desplegadas. Comprueba que el
commit y la etiqueta son los que publicaste.

### 4.3 Secretos

**Genéralos en el propio servidor**, así no viajan por ningún sitio:

```bash
cd /opt/subvdgda/docker

cat > .env <<EOF
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 24)
MYSQL_DATABASE=bdns_dgda
MYSQL_USER=bdns_user
MYSQL_PASSWORD=$(openssl rand -hex 24)
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://tu-dominio.org,https://www.tu-dominio.org
SITE_URL=https://tu-dominio.org
EOF

chmod 600 .env
sed 's/=.*/=***/' .env      # comprobar sin enseñar los valores
```

El `EOF` del principio va **sin comillas**: es lo que hace que los `openssl` se
ejecuten en vez de guardarse como texto.

Las variables SMTP se pueden dejar para después; sin ellas el correo cae en
Mailpit. Están documentadas en `docker/.env.example`.

### 4.4 Instalar

```bash
cd /opt/subvdgda
bash install.sh
```

Responde:

| Pregunta | Respuesta |
|---|---|
| ¿Continuar? | `s` |
| ¿Añadir el dominio local a `/etc/hosts`? | **`N`** — eso es para desarrollo |
| Email de administración | **uno real** |
| Contraseña | fuerte, guardada antes de pegarla |

**El email tiene que ser real.** Desde que no hay credenciales en el código, el
enlace de recuperación es la única forma de recobrar el acceso.

Si falta `python3.12-venv`, instálalo: el cargador del dataset se ejecuta desde
un entorno virtual porque necesita PyMySQL.

---

## Fase 5 — HTTPS con Let's Encrypt

**Es la única pieza que hay que construir**; el resto del despliegue es
configurar.

### El orden, y por qué

Let's Encrypt comprueba que el dominio es tuyo pidiéndote publicar un fichero
en `http://tu-dominio.org/.well-known/acme-challenge/...`. Ahí está el huevo y
la gallina: **esa comprobación va por HTTP**, porque cuando la haces todavía no
tienes certificado. Y este Nginx redirige todo el HTTP a HTTPS.

Por eso: primero se abre esa ruta, **se comprueba que funciona**, y solo después
se pide el certificado. Si se pide a ciegas y falla, Let's Encrypt limita los
reintentos.

### 5.1 Preparar

```bash
apt install -y certbot
mkdir -p /var/www/certbot/.well-known/acme-challenge
```

La ruta del reto **ya viene en el repositorio** (`docker/nginx/default.conf`,
dentro del bloque `listen 80` y antes de la redirección). Lo que hay que crear
es la configuración propia del servidor, que git no versiona:

```bash
cd /opt/subvdgda/docker
cp docker-compose.override.yml.example docker-compose.override.yml
```

Ese fichero añade los volúmenes de `/etc/letsencrypt` y `/var/www/certbot`.
Docker Compose lo lee y lo fusiona solo, sin pasarle ningún parámetro.

Aplica y **comprueba antes de seguir**:

```bash
cd /opt/subvdgda/docker && docker compose up -d nginx
echo prueba > /var/www/certbot/.well-known/acme-challenge/prueba
curl -s http://tu-dominio.org/.well-known/acme-challenge/prueba   # debe decir: prueba
```

### 5.2 Pedir el certificado

```bash
certbot certonly --webroot -w /var/www/certbot \
  -d tu-dominio.org -d www.tu-dominio.org \
  --email TU-CORREO --agree-tos --no-eff-email

rm -f /var/www/certbot/.well-known/acme-challenge/prueba
```

El correo es donde Let's Encrypt avisa si un certificado va a caducar sin
renovarse: es tu única alerta si la renovación automática falla.

### 5.3 Usarlo

**Las rutas del certificado NO se editan en `default.conf`.** Son lo único que
difiere entre desarrollo y producción, así que viven en un fichero aparte que se
incluye; el repositorio trae la versión de desarrollo en `docker/nginx-tls/` y
el servidor monta otra carpeta encima:

```bash
cd /opt/subvdgda/docker
mkdir -p nginx-tls-prod
cat > nginx-tls-prod/letsencrypt.conf <<'FIN'
ssl_certificate     /etc/letsencrypt/live/tu-dominio.org/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/tu-dominio.org/privkey.pem;
FIN

docker compose up -d nginx
docker exec bdns_nginx nginx -t
```

Se monta la carpeta `/etc/letsencrypt` **entera** y no los ficheros sueltos: los
de `live/` son enlaces simbólicos a `archive/` y **cambian de destino al
renovar**. Montando un fichero suelto, el contenedor seguiría sirviendo el
certificado viejo para siempre.

**Por qué toda esta separación:** así el servidor es una **copia limpia del
repositorio**. No tiene ni un fichero versionado modificado, y `git pull` entra
siempre sin conflictos. Todo lo específico de producción vive en
`docker-compose.override.yml` y `docker/nginx-tls-prod/`, que están en
`.gitignore`.

### 5.4 El enganche de la renovación

> **Esto es lo que más se olvida y lo que más tarde se descubre.**
> Certbot renovará el certificado solo, pero **Nginx no se entera**: lo mantiene
> cargado en memoria y seguiría sirviendo el caducado. El fallo aparece meses
> después, cuando ya nadie recuerda haber tocado nada.

```bash
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh <<'EOF'
#!/bin/sh
docker exec bdns_nginx nginx -s reload
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

certbot renew --dry-run
```

El ensayo hace el proceso completo contra el servidor de pruebas —incluido el
hook— sin gastar certificado real. Debe acabar con
`Congratulations, all simulated renewals succeeded`.

---

## Fase 6 — Comprobar desde fuera

**Desde otra máquina**, no desde el servidor. Lo que importa es lo que ve
internet:

```bash
# La web responde y redirige bien
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" http://tu-dominio.org
curl -s -o /dev/null -w "%{http_code}\n" https://tu-dominio.org        # sin -k: valida el certificado

# El certificado es el bueno
echo | openssl s_client -connect tu-dominio.org:443 -servername tu-dominio.org 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates

# Y lo más importante: que lo que debe estar cerrado, lo esté
for p in 3307 8080 8025 1025; do
  timeout 5 bash -c "echo > /dev/tcp/LA.IP/$p" 2>/dev/null \
    && echo "$p ABIERTO — MAL" || echo "$p cerrado"
done
```

**Mailpit (`8025`) abierto es el fallo más grave posible**: cualquiera pide una
recuperación de contraseña en la web, abre el buzón, lee el enlace y se hace
administrador sin adivinar nada.

---

## Fase 7 — Snapshot

Con la web ya funcionando, haz un snapshot en el panel del proveedor. Es el
punto de retorno si más adelante tocas algo y lo rompes.

En la descripción, apunta **qué recuperas**, no solo la fecha: qué versión está
desplegada, qué falta por configurar, y que restaurar **revierte también la base
de datos** a ese momento.

**Cuándo rehacerlo.** Los planes suelen incluir un solo snapshot, así que el
nuevo sustituye al viejo. Conviene refrescarlo **cuando el servidor cambie de
verdad** —una configuración nueva, un cambio grande de versión—, no en cada
publicación. Un snapshot que devuelve el servidor a un estado sin configurar
deja de ser un punto de retorno útil.

Y no lo gastes a mitad de un montaje: espera a que el servidor esté completo y
funcionando.

---

## Reconciliar un servidor desplegado antes de esta separación

Si el servidor se montó editando `default.conf` y `docker-compose.yml` a mano
—como ocurrió en el despliegue original—, esos dos ficheros versionados están
modificados y **el primer `git pull` fallará**. Se arregla una sola vez:

```bash
cd /opt/subvdgda
pwd                                             # comprobar: /opt/subvdgda

# 1. Guardar las rutas del certificado ANTES de descartar nada
mkdir -p docker/nginx-tls-prod
grep ssl_certificate docker/nginx/default.conf > docker/nginx-tls-prod/letsencrypt.conf
cat docker/nginx-tls-prod/letsencrypt.conf     # comprobar que son las dos líneas

# 2. Descartar las modificaciones locales de los ficheros versionados
git status                                      # ver qué hay modificado
git checkout -- docker/nginx/default.conf docker/docker-compose.yml

# 3. Traer la versión nueva
git pull

# 4. AHORA crear la configuración propia del servidor: el fichero de ejemplo
#    llega con el pull, antes no existe
cp docker/docker-compose.override.yml.example docker/docker-compose.override.yml

# 5. Comprobar antes de aplicar
git status                                      # debe salir "working tree clean"
cat docker/nginx-tls-prod/letsencrypt.conf

# 6. Aplicar
cd docker && docker compose up -d nginx
docker exec bdns_nginx nginx -t
```

**Dos cosas del orden que no son negociables:**

**El paso 1 va primero.** El paso 2 descarta el fichero donde están escritas esas
rutas; al revés, hay que volver a escribirlas a mano.

**El paso 4 va después del `git pull`.** El fichero de ejemplo forma parte del
commit nuevo, así que **antes del pull no existe** y el `cp` falla.

Y **no adelantes el paso 6**: entre el `pull` y el `cp`, la configuración del
repositorio apunta al certificado de desarrollo. Si recreas Nginx en ese momento,
arranca sirviendo el autofirmado y la web sale con aviso de «no seguro» hasta que
lo arregles. Mientras no toques el contenedor, sigue funcionando con lo que ya
tenía cargado: no hay corte.

Comprueba desde **otra máquina** que el certificado sigue siendo el bueno:

```bash
echo | openssl s_client -connect tu-dominio.org:443 -servername tu-dominio.org 2>/dev/null \
  | openssl x509 -noout -issuer -dates
```

A partir de aquí `git status` en el servidor debe salir limpio, y actualizar es
solo `git pull`.

---

## Mantenimiento

### Llegar a Adminer y Mailpit

No están expuestos, y así debe seguir. Se llega por túnel SSH desde tu equipo:

```bash
ssh -L 8080:localhost:8080 -L 8025:localhost:8025 servidor
```

Con el túnel abierto, `http://localhost:8080` en **tu** navegador es el Adminer
del servidor. Solo entra quien pueda entrar por SSH, y los túneles desaparecen
al cerrar la sesión.

Merece la pena dejarlo como atajo en tu `~/.ssh/config`, y así basta escribir
`ssh tuneles`:

```
Host tuneles
    HostName LA.IP.DEL.SERVIDOR
    User root
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    LocalForward 8080 localhost:8080
    LocalForward 8025 localhost:8025
```

> **Para antes tus contenedores locales: `make stop`.**
> Tu equipo tiene su propio Adminer y su propio Mailpit **en esos mismos
> puertos**. Con los dos en marcha, `localhost:8080` te enseña el de casa y no
> el del servidor — y no hay forma de distinguirlos a simple vista. Es el error
> más fácil de cometer aquí: creer que estás mirando producción cuando miras tu
> portátil.

Para entrar en Adminer necesitas las credenciales de la base de datos del
servidor, que están solo allí (`cat /opt/subvdgda/docker/.env`):

| Campo | Valor |
|---|---|
| Motor | MySQL |
| **Servidor** | **`db`**, no `localhost` — es el nombre del contenedor en la red interna de Docker |
| Usuario y contraseña | los `MYSQL_USER` y `MYSQL_PASSWORD` del `.env` |
| Base de datos | `bdns_dgda` |

### Actualizar a una versión nueva

```bash
cd /opt/subvdgda
git pull
cd docker && docker compose up -d --build backend
```

El backend va **horneado en la imagen**: un `restart` seguiría ejecutando el
código viejo. El frontend, en cambio, es un montaje directo y se actualiza solo.

### Copias de seguridad

```bash
cd /opt/subvdgda && make backup
```

Deja el volcado en `backups/`, ignorado por git. Cópialo fuera del servidor de
vez en cuando: un backup que vive en la misma máquina que la base de datos no
protege del incendio.

### Comprobar el cron

```bash
docker logs bdns_cron --tail 20
docker exec bdns_cron date
```

Las tareas están programadas en **UTC**. En horario de verano español eso son
dos horas menos que tu reloj.

---

## Errores que nos encontramos

Todos reales, todos en el despliegue del 15-ago-2026.

| Qué pasó | Por qué | Cómo se evita |
|---|---|---|
| `ssh-copy-id` instaló una clave ajena | Elige por su cuenta si no le dices cuál | Usar `-i ruta.pub` siempre |
| El mensaje de error de `make` no salía | `make` usa `dash`, donde `.` sobre un fichero inexistente mata el shell antes del `||` | Comprobar con `[ -f fichero ]` antes de cargarlo |
| `install.sh` abortó tras leer 6396 registros | El cargador leía `DB_PASSWORD` y el `.env` define `MYSQL_PASSWORD`; en local coincidían por casualidad con el valor escrito en el código | Que los scripts acepten los dos juegos de nombres |
| `make backup` fallaba en el servidor | Credenciales escritas a fuego en el `Makefile` | Cargar `docker/.env` en cada receta |
| Faltaba `python3.12-venv` | El cargador del dataset corre en un entorno virtual | Instalarlo antes; no es opcional |
| El reto de Let's Encrypt fracasaba | Nginx redirigía a HTTPS también esa ruta | Abrir `/.well-known/acme-challenge/` antes de pedir el certificado |

Y la lección que las agrupa a casi todas: **un valor por defecto escrito en el
código que coincide con el del entorno de desarrollo esconde el fallo hasta que
despliegas de verdad.** Los dos caminos dan el mismo resultado y nadie se entera
de que uno está mal.
