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

### Trabajar en el servidor por SSH

Tres costumbres que evitan los errores más tontos, todos cometidos al menos una
vez:

**1. Espera a ver el prompt antes de escribir.** Al conectar hay varios segundos
—la passphrase, el saludo del proveedor, el mensaje del sistema— en los que el
teclado no va a donde crees. Si escribes durante esa espera, los comandos se
pierden por el camino y acabas ejecutando solo el último.

**Nada de pegar varias líneas de golpe** por el mismo motivo: una a una,
esperando a que vuelva el prompt entre cada una.

**2. Comprueba dónde estás antes de tocar ficheros.** El prompt lo dice:

| Lo que ves | Dónde estás |
|---|---|
| `root@servidor:~#` | En `/root`, la carpeta personal |
| `root@servidor:/opt/subvdgda#` | En el proyecto ← aquí es donde hay que estar |

Ante la duda, `pwd`. Si un comando responde «No such file or directory» y sabes
que el fichero existe, casi siempre es esto.

**3. Editar sin editor cuando es una línea.** Para añadir algo al final de un
fichero de configuración:

```bash
echo "VARIABLE=valor" >> docker/.env
tail -3 docker/.env          # comprobar que quedó en su propia línea
```

Evita abrir `nano` y evita guardar sin querer en el sitio equivocado. Para
cambios más grandes, la extensión **Remote - SSH** de VS Code permite editar los
ficheros del servidor con el editor de siempre.

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

Los datos que se olvidan entre despliegue y despliegue, primero:

| Qué | Valor |
|-----|-------|
| Conectar | `ssh servidor` (el alias está en tu `~/.ssh/config`, apunta a la IP) |
| Ruta del proyecto | `/opt/subvdgda` — **no** el home de root |
| Desde dónde se lanza compose | `/opt/subvdgda/docker`, y así no hace falta `-f` |
| Rama que sigue el servidor | `main` (compruébalo con `git branch --show-current`) |

La secuencia completa:

```bash
ssh servidor
cd /opt/subvdgda
git branch --show-current      # debe decir main; si no, parar y mirar por qué
git pull

cd docker
docker compose up -d --build backend       # solo si cambió código Python
docker compose exec nginx nginx -s reload  # solo si cambió la config de Nginx
```

**No todos los pasos hacen falta siempre**, y saber cuál toca evita tanto
reconstruir de más como quedarse corto:

| Qué has cambiado | Qué hay que hacer |
|------------------|-------------------|
| HTML, CSS, JS del frontend | **nada** — es un montaje directo, el `git pull` ya lo aplica |
| Cualquier `.py` del backend | `docker compose up -d --build backend` |
| `docker/nginx/default.conf` | `docker compose exec nginx nginx -s reload` |
| Variables de `docker/.env` | `docker compose up -d` del servicio afectado |
| **`depends_on` o `restart` en compose** | `docker compose up -d --force-recreate <servicio>`. Un `up -d` normal **no** los aplica: solo recrea si cambió la imagen o el entorno |
| **Columnas nuevas en la BD** | **migración SQL — ver abajo.** El `git pull` NO las crea |
| **Correcciones de datos ya cargados** | **migración SQL — ver abajo.** `cargar_dataset` es aditivo y no reescribe filas |

El backend va **horneado en la imagen**: un `restart` seguiría ejecutando el
código viejo, por eso `--build`. Nginx, en cambio, mantiene su configuración
**cargada en memoria**: sin el `reload` sigue aplicando la anterior aunque el
fichero ya esté actualizado en disco.

Ese segundo caso es el traicionero, porque el fallo no se parece a su causa.
Si un despliegue borra un archivo del frontend y añade una regla de Nginx que
lo sustituye —como pasó al convertir `solicitudes.html` en redirección—, entre
el `git pull` y el `reload` hay unos segundos en que esa ruta da 404: el
archivo ya no está y la regla que ocupa su lugar todavía no se ha cargado.

#### Cuando el despliegue trae cambios de esquema o de datos

Estos dos casos son los traicioneros, porque **parecen un `git pull` normal y no
lo son**. Conviene entender por qué antes de ejecutar nada.

`modelo-fisico.sql` está montado en `/docker-entrypoint-initdb.d/`, y MariaDB
solo ejecuta lo que hay ahí **cuando el directorio de datos está vacío**. En un
servidor con datos no se vuelve a ejecutar nunca, así que **una columna nueva no
aparece sola**. Pero el modelo ORM sí la mapea, de modo que la API pediría
`SELECT ... columna_nueva ...` contra una tabla que no la tiene: error 1054 y
**500 en la portada**.

Y `cargar_dataset` no sirve para arreglarlo: es **aditivo**. Inserta lo que falta,
pero no reescribe filas existentes, así que no corrige nombres ni fusiona
entidades duplicadas.

> **Nunca `reset-db` en el servidor.** Borraría la cuenta de administración y las
> `fecha_fin_plazo`, que no están en el dataset y se rellenan a mano desde el
> panel. En local eso se recupera del backup; en producción es un susto.

Las migraciones viven en `scripts/migraciones/`, con la fecha en el nombre. Son
idempotentes: lanzarlas dos veces no estropea nada.

**Cómo saber si el despliegue que viene necesita una**, cómo escribirla y cómo
ensayarla contra una réplica del servidor antes de tocarlo: `docs/migraciones.md`.
La comprobación rápida, antes de desplegar, es si el esquema o el modelo ORM
cambiaron desde la última etiqueta desplegada:

```bash
git diff v1.6..main -- docker/init/modelo-fisico.sql backend/app/models.py
```

Si eso tiene salida, hace falta migración. Sin excepción.

```bash
ssh servidor
cd /opt/subvdgda
git pull

# 1. Backup ANTES de tocar nada
bash scripts/backup_db.sh

# 2. La migración (ajusta el nombre del fichero)
#
#    OJO A LAS COMILLAS SIMPLES. Las variables MYSQL_* viven en docker/.env, no
#    en tu shell: si se usan comillas dobles las expande el shell del servidor,
#    llegan vacías y mariadb toma el «-p» como nombre de usuario
#    («ERROR 1045: Access denied for user '-p'@'localhost'»). Con comillas
#    simples las expande el `sh` de dentro del contenedor, que sí las tiene.
cd docker
docker compose exec -T db sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' \
    < ../scripts/migraciones/2026-08-23_periodo_y_erratas.sql

# 3. El backend, que va horneado en la imagen
docker compose up -d --build backend

# 4. Comprobar que la API responde con los campos nuevos
curl -s https://subvencionesdgda.org/convocatorias/ | head -c 400
```

**El orden importa**: si se reconstruye el backend antes de migrar, queda
sirviendo 500 hasta que la migración pase.

#### Comprobar que ha llegado de verdad

Que los contenedores digan `Started` no prueba que el cambio esté aplicado.
Conviene verificar lo que se acaba de tocar:

```bash
# La API responde y sirve datos reales
curl -s https://subvencionesdgda.org/avisos/ | head -c 120

# Una redirección conserva los parámetros (si tocaste reglas de Nginx)
curl -sI "https://subvencionesdgda.org/solicitudes.html?buscar=gata" | grep -i location
```

En la redirección, lo que hay que mirar no es que responda, sino que el
`Location` conserve el `?buscar=gata`. Una redirección que pierde la query
string funciona y aun así no sirve: los enlaces guardados con filtros —lo
único que justifica mantener la ruta— aterrizarían en un buscador vacío.

### Copias de seguridad

**A mano**, cuando vayas a hacer algo arriesgado:

```bash
cd /opt/subvdgda && make backup
```

> **Este `crontab` es el de Linux, no el fichero `docker/cron/crontab` del
> proyecto.** Ese segundo **no lo ejecuta nadie**: el contenedor arranca un
> `scheduler.py` propio y aquel fichero solo documenta la programación
> original. La copia de seguridad va en el `crontab` del sistema porque
> necesita hablar con el contenedor de MariaDB, y eso desde dentro del
> contenedor de cron exigiría darle acceso al demonio de Docker.

**Programado**, una vez, para que se haga solo. Primero fija cuánto tiempo se
conservan las copias, en `docker/.env` del servidor:

```
BACKUP_DIAS=180
```

Y después la tarea:

```bash
crontab -e
```

```
30 3 * * 0 /opt/subvdgda/scripts/backup_db.sh >> /opt/subvdgda/logs/cron/backup_db.log 2>&1
```

Eso es **los domingos a las 03:30**. Las 03:30 no coinciden con las otras tareas
del proyecto —la rotación de logs a las 04:15 y la comprobación de BDNS a las
08:00—, así que nunca se solapan. Recuerda que **el servidor va en UTC**: en
horario de verano español, eso son las 05:30.

> **Frecuencia y retención van unidas, y es lo que más se hace mal.**
> Con copias semanales y 30 días de retención te quedan **solo cuatro**: si
> descubres un problema a las seis semanas, no hay nada que restaurar. Al
> espaciar la frecuencia hay que alargar la retención. Semanal + 180 días son
> unas 26 copias cubriendo medio año, y ocupan ~21 MB.

**Por qué semanal y no diaria.** Depende de cada cuánto cambian los datos que
*no* se pueden reconstruir. Aquí el dataset se versiona en git, y `make reset-db`
—la operación más arriesgada— ya hace su propio backup antes de borrar. Lo que
la copia programada protege de verdad es lo impredecible: que el cron descubra
una convocatoria nueva un día cualquiera. Semanal cubre eso de sobra; diaria
sería ruido.

**La retención se pone en el `.env` y no en la línea del cron** a propósito: así
vale igual para la tarea programada y para un `make backup` lanzado a mano. Al
revés, ese `make backup` manual usaría el valor por defecto y **borraría copias
que querías conservar**.

Comprueba al día siguiente que corrió:

```bash
cat /opt/subvdgda/logs/cron/backup_db.log
ls -lh /opt/subvdgda/backups/
```

**Qué hace el script**, más allá de volcar:

- **Descarta un volcado incompleto.** Que el comando termine bien no basta: un
  corte a mitad —disco lleno, contenedor parado— deja un fichero truncado con
  pinta de válido. Comprueba la marca de cierre que escribe `mariadb-dump` al
  final, y si no está, borra el fichero en vez de guardarlo.
- **Rota**: elimina los de más de 30 días, para que un volcado diario no acabe
  llenando el disco. Se ajusta con `BACKUP_DIAS`.

### Informe de visitas

Quién entra, qué mira y desde dónde llega, **sin cookies ni servicios externos**:
todo sale de los registros que Nginx ya escribe y que `privacidad.html` declara.

Se instala **una vez** y queda para siempre:

```bash
apt install goaccess
```

Y se genera cuando quieras:

```bash
cd /opt/subvdgda && make informe-visitas
```

Deja `informes/visitas-AAAA-MM-DD.html`. Se abre en el navegador y trae páginas
más vistas, visitantes únicos por día, procedencia, navegadores y dispositivos,
códigos de error y las páginas más lentas.

**Programado**, para no acordarte de lanzarlo. Retención en `docker/.env`:

```
INFORMES_DIAS=365
```

Y la tarea, en el mismo `crontab -e` que la copia de seguridad (el de Linux):

```
0 4 * * 1 /opt/subvdgda/scripts/informe_visitas.sh >> /opt/subvdgda/logs/cron/informe_visitas.log 2>&1
```

Lunes a las 4:00, media hora después de la copia del domingo para no solaparse.

#### Dos informes, para dos cosas distintas

| | `make resumen-visitas` | `make informe-visitas` |
|---|---|---|
| Qué es | resumen propio, **en español** | GoAccess, detalle completo en inglés |
| Tamaño | ~10 KB | ~900 KB |
| Necesita | solo Python | `apt install goaccess` |
| Para | el vistazo semanal | investigar algo concreto |

El resumen responde a cinco preguntas y se acaba: cuánta gente entra, qué mira,
de dónde llega, con qué dispositivo y qué está fallando. Descuenta los robots y
los ficheros estáticos, porque contarlos infla las cifras hasta dejarlas sin
sentido: en una web pública la mayor parte del tráfico es automático, y una
sola visita pide veinte ficheros entre imágenes, estilos y scripts.

```bash
cd /opt/subvdgda
make resumen-visitas                            # últimos 30 días
python3 scripts/resumen_visitas.py --dias 7     # solo la última semana
python3 scripts/resumen_visitas.py --organizaciones   # + administraciones públicas
```

El botón **«Guardar como PDF»** del propio informe usa la impresión del
navegador, que ya sabe generar PDF. No hay opción de imagen: haría falta una
librería externa y el informe dejaría de abrirse sin conexión; para una imagen,
una captura de pantalla hace lo mismo.

#### Identificar administraciones públicas

`--organizaciones` resuelve el nombre de red (DNS inverso) de los visitantes
habituales y busca si pertenece a una administración: ayuntamientos,
diputaciones, comunidades autónomas, Estado, universidades públicas.

**Identifica organizaciones, no personas.** Nunca se muestra la dirección IP,
solo el organismo y cuántas páginas ha visto. Que un ayuntamiento consulte los
datos de sus propias subvenciones es información legítima y de interés público.

Va **desactivado por defecto** por dos razones: cada visitante habitual supone
una consulta de red, así que tarda; y no siempre aporta.

**Y hay que leerlo con cuidado**: la mayoría de administraciones navegan con
conexiones comerciales corrientes, indistinguibles de una casa. Que un
ayuntamiento **no** aparezca no significa que no haya entrado — significa que
su red no lo dice. Sirve para confirmar que alguien entró, nunca para concluir
que nadie lo hizo.

Los patrones están comprobados en los tests contra nombres reales de organismos
y, sobre todo, contra conexiones domésticas y comerciales que **no** deben
identificarse: un falso positivo sería peor que no detectar nada.

#### Países y ciudades (GeoLite2 de MaxMind)

Es **opcional**: sin esto, el resumen se genera igual y lo dice en su propia
sección, explicando qué falta. Nada más depende de ello.

**Una vez, en tu cuenta de MaxMind:**

1. Registrarse en `https://www.maxmind.com/en/geolite2/signup` (gratis).
2. **Manage License Keys** → *Generate new license key*.
3. **Download Files** → **GeoLite2-City**, formato GZIP (el `.mmdb`, no el CSV).

**Subirla al servidor:**

```bash
# En tu ordenador, tras descomprimir el .tar.gz
scp GeoLite2-City.mmdb servidor:/opt/subvdgda/datos/geoip/
```

Si la carpeta no existe: `ssh servidor 'mkdir -p /opt/subvdgda/datos/geoip'`.

**Y la librería, una vez:**

```bash
ssh servidor
pip install maxminddb          # o apt install python3-maxminddb
```

A partir de ahí, `make resumen-visitas` incluye las secciones de país y ciudad
sin más. Para usar otra ruta, la variable `GEOIP_DB`.

**En GoAccess** es un parámetro más, si ese binario trae soporte compilado
(compruébalo con `goaccess --help | grep -i geoip`):

```bash
goaccess ... --geoip-database=/opt/subvdgda/datos/geoip/GeoLite2-City.mmdb
```

##### La segunda base: separar personas de centros de datos

Con solo la base de ciudades, el informe engaña. Al activarla por primera vez,
entre las ciudades con más «visitas» aparecían **Ashburn, Boardman, Santa Clara
y Phoenix**, que no son sitios donde vive gente leyendo sobre subvenciones sino
donde están los centros de datos de Amazon, Google y Microsoft. Estados Unidos
encabezaba la lista con casi el triple de visitas que España.

Eran rastreadores y escáneres alojados en la nube que, **a diferencia de
Googlebot, no se identifican como robots** en su agente de usuario, así que el
filtro de robots no los veía.

Se corrige con la segunda base gratuita, **GeoLite2-ASN**, que dice a qué red
pertenece cada dirección. Misma página de descargas, fila **GeoLite ASN**,
formato GZIP:

```bash
scp GeoLite2-ASN_*/GeoLite2-ASN.mmdb servidor:/opt/subvdgda/datos/geoip/
```

A partir de ahí, ese tráfico se descuenta de todas las cifras igual que los
robots, y aparece en su propia sección para que se vea cuánto era.

El reconocimiento va por el nombre de la red, porque la base gratuita no marca
«esto es alojamiento». No es exhaustivo —salen proveedores nuevos
constantemente— pero cubre a los grandes. Los tests comprueban las dos
direcciones, y **la segunda importa más**: que Telefónica, Orange, Vodafone o
MásMóvil **no** se confundan con centros de datos, porque eso borraría del
informe justo a las personas que entran desde casa.

##### Repasar el filtro de vez en cuando

**Esto nunca queda terminado**: salen proveedores de alojamiento nuevos
constantemente. Cada pocos meses, o cuando un país raro encabece la lista sin
que ninguna de sus ciudades aparezca —esa es la señal—, conviene mirar qué
redes están pasando:

```bash
ssh servidor
cd /opt/subvdgda
python3 -c "
import maxminddb, re, collections
from pathlib import Path
asn = maxminddb.open_database('datos/geoip/GeoLite2-ASN.mmdb')
c = collections.Counter()
for f in Path('logs/nginx').glob('access.log*'):
    for l in f.read_text(errors='replace').splitlines():
        m = re.match(r'(\S+) ', l)
        if not m: continue
        o = (asn.get(m.group(1)) or {}).get('autonomous_system_organization')
        if o: c[o] += 1
for red, n in c.most_common(25): print(f'{n:>6}  {red}')
"
```

Al leer esa lista, **lo importante no es qué añadir sino qué no tocar**. En la
primera revisión, la red con más peticiones de todas las que pasaban el filtro
era `Digi Spain Telecom` con 554: un operador español de consumo, o sea
personas en su casa. Añadirlo habría «limpiado» las cifras borrando justo a los
visitantes reales.

La regla: **ante la duda, dejarlo pasar**. Contar de más se nota y se corrige;
borrar a una persona no se ve nunca.

Los nombres nuevos se añaden a `REDES_NUBE`, en `scripts/resumen_visitas.py`,
y conviene meterlos también en el test junto a los que no deben filtrarse.

##### Qué fiabilidad tiene

**El país es fiable.** La ciudad **no**: es una aproximación, y con conexiones
móviles suele señalar por dónde sale el tráfico de la operadora, no dónde está
la persona. Sirve para hacerse una idea, no para afirmar nada.

La base **no se versiona** —pesa decenas de MB y tiene licencia propia de
MaxMind—: está en `.gitignore` y cada instalación descarga la suya. Conviene
actualizarla un par de veces al año, porque los rangos de IP cambian.

#### La forma corta: `make informes`

Desde tu ordenador, en una sola orden: genera el informe en el servidor, se lo
trae a `informes/servidor/` y lo abre en el navegador.

```bash
make informes                 # últimos 7 días
make informes DIAS=30         # otro periodo
make informes TIPO=goaccess   # el informe completo, con navegadores y errores
make informes ABRIR=no        # solo descargar
```

**Ojo con no confundir dos cosas.** `informes/` guarda los informes **locales**,
sacados de los registros del Docker de desarrollo: son tu propio trasteo, no
visitas. Los del servidor van aparte, en `informes/servidor/`. La diferencia se
ve sola —en agosto de 2026, 1.112 peticiones en local frente a 16.569 en el
servidor—, pero mezclarlos lleva a conclusiones falsas.

Y el aviso de siempre: **los informes llevan direcciones IP**. Por eso se
escriben fuera de la carpeta que sirve Nginx y `informes/` está en `.gitignore`.
No los subas a ningún sitio público.

#### Cómo abrirlos

Los informes **no son accesibles desde la web**, y es a propósito: contienen
direcciones IP. Nginx solo sirve `frontend/`, e `informes/` queda fuera.

**Opción 1 — traértelos a tu ordenador** (la habitual). Desde tu máquina, no
desde la sesión SSH:

```bash
mkdir -p ~/informes-subvdgda
scp servidor:/opt/subvdgda/informes/*.html ~/informes-subvdgda/
```

Y para abrirlos, estando en WSL, hay tres caminos:

```bash
explorer.exe ~/informes-subvdgda          # abre la carpeta en Windows
cd ~/informes-subvdgda && explorer.exe resumen-2026-08-16.html   # abre el fichero
```

O navegando: pega `\\wsl$\Ubuntu\home\ubuntu\informes-subvdgda` en la barra de
direcciones del explorador de Windows. Merece la pena anclar esa ruta a Acceso
rápido, porque los ficheros de WSL **no están en el disco de Windows** y no se
llega a ellos navegando por las carpetas de siempre.

Windows los abrirá con Edge si es tu navegador por defecto. Para usar otro,
clic derecho sobre el fichero → Abrir con.

**Opción 2 — leerlo por un túnel SSH**, sin descargar nada. Útil si estás en
otro ordenador. Desde tu máquina:

```bash
ssh -L 8090:localhost:8090 servidor
```

Y ya dentro del servidor:

```bash
cd /opt/subvdgda/informes && python3 -m http.server 8090 --bind 127.0.0.1
```

Ahora abres `http://localhost:8090` en tu navegador. El `--bind 127.0.0.1` es
importante: sin él el servidor quedaría escuchando en todas las interfaces y
los informes, con sus IPs dentro, serían accesibles desde internet. Al terminar,
`Ctrl+C` y cierras la sesión.

**Opción 3 — verlo en texto por la terminal**, sin salir del servidor:

```bash
goaccess logs/nginx/access.log* --log-format='%h %^[%d:%t %^] "%r" %s %b "%R" "%u" %T' \
  --date-format='%d/%b/%Y' --time-format='%H:%M:%S' --num-tests=0
```

Se abre en modo interactivo dentro de la terminal: flechas para moverse, `q`
para salir. Es el mismo dato, sin generar fichero.

#### Lo que hay que saber para no sacar conclusiones falsas

**Las IPs no son personas.** Una puede ser una casa entera o una operadora
móvil con miles de clientes. Sirve para tendencias, no para contar gente.

**Los rastreadores se descuentan** (`--ignore-crawlers`), pero solo los
conocidos. En una web nueva, buena parte del tráfico restante seguirá siendo
automático.

**Solo hay 30 días de registros.** `rotar_logs.py` borra lo anterior, y ese
número está en `privacidad.html`. Los informes sí se conservan un año, así que
para series largas lo que vale es guardar los informes, no los registros.

**El sexo o la edad del visitante no se pueden saber**, ni con esto ni con
nada que no sea perfilado publicitario. En una petición HTTP no viaja esa
información.

#### Si el informe sale vacío

El script se planta y avisa. Pasa si alguien cambia `log_format` en
`docker/nginx/default.conf` sin tocar el `FORMATO` del script: GoAccess deja
de reconocer las líneas. Los dos van juntos, y hay tests que lo comprueban.

### Visibilidad: buscadores y rastreadores de IA

Tener la web publicada no basta para que se encuentre. Esta sección recoge qué
hay puesto, por qué, y qué hacer cuando algo no aparece.

#### Los dos ficheros

| Fichero | Qué hace |
|---|---|
| `frontend/robots.txt` | Dice a los rastreadores qué pueden visitar. **Es una petición, no una barrera**: los rastreadores serios la respetan, los maliciosos la ignoran. Nunca sirve como medida de seguridad |
| `frontend/sitemap.xml` | Lista las páginas públicas para que los buscadores no dependan de ir siguiendo enlaces |

Al **añadir una página pública hay que añadirla al sitemap**. Un test lo
comprueba (`test_sitemap_lista_todas_las_paginas_publicas`), así que si se
olvida, la batería falla.

En el sitemap, la frecuencia declarada (`changefreq`) es **deliberadamente
conservadora**: `monthly` y `yearly`, nunca `daily`. Los datos se actualizan dos
veces al año, y anunciar más movimiento del real hace que los buscadores dejen
de fiarse de esa señal y la ignoren.

#### La decisión sobre los rastreadores de IA

**Se permiten todos, a propósito.** El informe de visitas mostró que OpenAI y
Anthropic rastrean más que ningún buscador —unas 250 peticiones frente a 17 de
Bing—, y se decidió dejarlos pasar: si estos datos aparecen en respuestas de
asistentes, el asunto gana visibilidad, que es para lo que existe el proyecto.

Conviene distinguir dos cosas que suelen confundirse:

| Tipo | Ejemplos | Qué aporta |
|---|---|---|
| **Entrenamiento** | `GPTBot`, `ClaudeBot`, `CCBot` | Difuso. Un modelo entrenado con miles de millones de páginas puede no recordar este análisis concreto |
| **Búsqueda en vivo** | `OAI-SearchBot`, `PerplexityBot`, `ChatGPT-User` | **Concreto: citan con enlace** y traen visitas |

El beneficio real viene de los segundos.

**Esta decisión va más allá de la licencia**, y eso está resuelto y no se debe
deshacer sin pensarlo. El contenido es CC BY-NC-ND: sin uso comercial y sin
obras derivadas. Entrenar un modelo comercial es ambas cosas. Sin más, la web
permitiría en la práctica lo que su propia licencia prohíbe.

Por eso el README y `aviso-legal.html` conceden un **permiso expreso adicional**
—quien tiene los derechos puede dar más de lo que la licencia da— explicando el
motivo. **Los tres textos tienen que decir lo mismo**: `robots.txt`, el aviso
legal y el README. Hay tests que lo verifican; si algún día se bloquea un
rastreador y se olvida actualizar los otros dos, la batería salta.

#### Una sola dirección para el sitio

El sitio responde en `subvencionesdgda.org` y en `www.subvencionesdgda.org`, y
Nginx redirige la segunda a la primera con un 301. Sin eso, Google las trata
como **dos webs distintas** y reparte entre ellas las señales de posicionamiento.

Las etiquetas `<link rel="canonical">` de las páginas no bastan por sí solas:
son una sugerencia, y mientras el servidor devuelva 200 en las dos variantes
pueden ignorarse. Aquí se ignoraron.

**Depende de algo que conviene no perder de vista: el certificado tiene que
cubrir las dos direcciones.** Si dejara de cubrir `www`, el navegador fallaría
en el saludo TLS *antes* de recibir la redirección, y quien entrara por `www`
vería un aviso de seguridad en vez de la web. Se comprueba así:

```bash
openssl s_client -connect subvencionesdgda.org:443 -servername subvencionesdgda.org </dev/null 2>/dev/null \
  | openssl x509 -noout -text | grep -A1 "Subject Alternative Name"
```

Tienen que aparecer los dos: `DNS:subvencionesdgda.org` y
`DNS:www.subvencionesdgda.org`. Si algún día se reemite el certificado, hay que
seguir pidiéndolo para ambos.

El reto de Let's Encrypt sigue sirviéndose sin redirigir en las dos direcciones
—va en un `location ^~`, que tiene prioridad—, así que la renovación no se ve
afectada. Comprobado.

Qué verificar tras desplegar un cambio en estas redirecciones:

```bash
for u in http://subvencionesdgda.org/ http://www.subvencionesdgda.org/ \
         https://www.subvencionesdgda.org/ https://subvencionesdgda.org/index.html \
         https://subvencionesdgda.org/; do
  echo "$u → $(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$u")"
done
```

Lo esperado: las cuatro primeras dan **301** y todas acaban en
`https://subvencionesdgda.org/`; la última da **200**. Si la última diera 301,
hay un bucle en la portada y hay que revertir.

#### Google Search Console

Es lo que de verdad mueve la aguja. Al publicar la web, Google **no la rastreó
en semanas**: en los registros solo aparecía Bing.

Una vez, al principio:

1. Entrar en `https://search.google.com/search-console` y añadir la propiedad
   `subvencionesdgda.org`.
2. Verificar que el dominio es tuyo (lo más simple es el registro DNS TXT que
   te da Google, que se añade en el panel de Cloudflare).
3. **Inspección de URLs** → pegar `https://subvencionesdgda.org/` → *Solicitar
   indexación*. Repetir con las páginas principales, sin pasarse: hay cupo
   diario.
4. **Sitemaps** → enviar `sitemap.xml` (solo eso; el dominio ya va delante).

> El sitemap hay que enviarlo **después de desplegarlo**. Si se envía antes,
> Google se encuentra un 404 y lo marca como erróneo.

**Los plazos son largos.** Search Console tarda un día en mostrar datos, y que
una página aparezca en los resultados lleva días o semanas. Que mañana siga
vacío no significa que algo falle.

#### Cómo saber si está funcionando

Sin entrar en Search Console, el propio informe de visitas lo dice:

```bash
make resumen-visitas
```

En la sección **«Robots y buscadores»**, que aparezca *Google (indexa la web)*
significa que ya está rastreando. Mientras no aparezca, no está pasando.

Y en **«De dónde llegan»**, si empieza a salir `google.com`, es que la web ya
sale en resultados y la gente pincha.

#### Si Google sigue sin aparecer

Lo más habitual no es un fallo técnico, sino que **nadie enlaza al sitio**.
Google descubre webs siguiendo enlaces, y un dominio nuevo sin ningún enlace
entrante tarda mucho en ser encontrado, aunque se pida la indexación.

En Search Console eso se ve en la inspección de una URL, en «Página de
referencia: No se ha detectado ninguna».

La solución no es técnica: conseguir que alguna web del sector enlace a esta.
Un enlace desde una asociación conocida vale más que cualquier ajuste.

### Sacar las copias del servidor

> **Un backup que vive en la misma máquina que la base de datos no protege de
> perder la máquina.** Es el punto que más se olvida: si el servidor se pierde,
> se pierden los dos a la vez.

Desde **tu ordenador**, para traerte el más reciente:

```bash
ssh servidor 'ls -t /opt/subvdgda/backups/*.sql | head -1' \
  | xargs -I{} scp servidor:{} ~/backups-subvdgda/
```

Hazlo de vez en cuando, o cuando hayas metido datos que te importen: usuarios
nuevos, fechas de plazo ajustadas a mano. Automatizarlo desde el portátil no
compensa, porque tendría que estar encendido a la hora justa.

### Restaurar

Lo que hay que saber **antes** de necesitarlo:

```bash
cd /opt/subvdgda
make restore FILE=backups/backup_AAAAMMDD_HHMMSS.sql
```

**Restaurar sobrescribe la base de datos actual.** Si tienes dudas de si el
volcado es bueno, pruébalo primero en una base de datos aparte, sin tocar la
real:

```bash
set -a; . docker/.env; set +a
docker exec bdns_dgda_db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "CREATE DATABASE prueba_restore;"
docker exec -i bdns_dgda_db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" \
  prueba_restore < backups/EL_FICHERO.sql
docker exec bdns_dgda_db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "SELECT COUNT(*) FROM prueba_restore.solicitudes;"
docker exec bdns_dgda_db mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" \
  -e "DROP DATABASE prueba_restore;"
```

Este procedimiento se probó el 16-ago-2026 con un volcado real: 6396
solicitudes y 11 tablas, idénticas al original.

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
