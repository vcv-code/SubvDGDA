# Sistema de autenticación

Documentación del sistema de autenticación JWT implementado en el backend.

→ Ver también: [Referencia técnica](referencia-tecnica.md) · [Tests automáticos](tests.md)

---

## Por qué JWT

Las APIs REST son **stateless** por diseño: el servidor no guarda estado entre peticiones. Esto significa que cada petición debe ir acompañada de algo que demuestre quién eres. JWT (JSON Web Token) es el mecanismo estándar para esto.

Un JWT es un texto firmado con la clave secreta del servidor que contiene: quién eres (`sub`), qué rol tienes y cuándo expira. El servidor puede validarlo sin consultar la BD — basta con verificar la firma.

---

## Access token y refresh token

El sistema usa **dos tokens** con propósitos distintos:

| | Access token | Refresh token |
|---|---|---|
| Duración | 15 minutos | 30 días |
| Dónde se valida | El backend verifica la firma JWT con la clave secreta | El backend busca el token en la tabla `refresh_tokens` de BD |
| Se guarda en BD | **No** — es stateless | **Sí** — necesita registro en BD para poder revocarlo |
| Si se roba | Válido máximo 15 minutos | Válido 30 días, pero se puede revocar |
| Para qué sirve | Llamar a cualquier endpoint protegido | Solo llamar a `/auth/refresh` y `/auth/logout` |

**Por qué el access token NO se guarda en BD:** el JWT es stateless por diseño. El servidor puede validarlo solo con la clave secreta, sin tocar la BD. Esto es lo que lo hace escalable — si hubiera varios servidores, cualquiera puede validar el token sin coordinarse. Si se guardara en BD, todas las peticiones tendrían que consultarla, lo que eliminaría la ventaja del JWT.

**Por qué el refresh token SÍ se guarda en BD:** necesitamos poder revocarlo (al hacer logout, al cambiar la contraseña, si la cuenta está comprometida). Un JWT no se puede "invalidar" antes de que expire — es solo texto firmado. Un registro en BD sí se puede marcar como `revocado = true`.

**Metáfora:** el access token es como un ticket de metro de un solo uso que caduca en 15 minutos. Si caduca, no sirve. El refresh token es como una tarjeta de transporte anual que te permite sacar tickets nuevos sin volver a pagar — pero si la pierdes, la pueden cancelar en el sistema.

---

## Flujo completo

```text
1. POST /auth/login  {email, password}
        ↓
   Verifica contraseña (bcrypt)
        ↓
   Genera access_token (JWT, 15 min)
   Genera refresh_token (token opaco, 30 días) → guarda en BD
        ↓
   Devuelve { access_token, refresh_token }
        ↓  (cliente guarda ambos en localStorage)

2. Petición autenticada
   GET /privado/perfil
   Authorization: Bearer <access_token>
        ↓
   Backend valida firma JWT → extrae email + rol
        ↓
   Respuesta 200

3. Access token caducado (15 min después)
   POST /auth/refresh  { refresh_token }
        ↓
   Backend busca refresh_token en BD
   Verifica: existe, no revocado, no expirado
        ↓
   Rotación: marca el token antiguo como revocado
   Genera access_token nuevo
   Genera refresh_token nuevo → guarda en BD
        ↓
   Devuelve { access_token, refresh_token }
        ↓  (cliente actualiza localStorage)

4. POST /auth/logout  { refresh_token }
        ↓
   Marca refresh_token como revocado en BD
   (fire-and-forget: el cliente borra localStorage sin esperar)
```

---

## Rotación del refresh token

Cuando se usa el refresh token para renovar la sesión, el token antiguo se revoca y se genera uno nuevo. Esto tiene un propósito de seguridad:

Sin rotación, si un atacante roba el refresh token puede usarlo durante 30 días sin que el usuario lo sepa.

Con rotación, si el atacante usa el token robado, el usuario legítimo también intentará usarlo (cuando su app renueve la sesión). La segunda petición con el token ya revocado falla con 401. El usuario es forzado a hacer login de nuevo y el token robado queda inútil.

```text
Atacante roba refresh_token "abc123"

Atacante lo usa:
  POST /auth/refresh { refresh_token: "abc123" }
  → BD: "abc123" existe, no revocado
  → "abc123" se revoca → se genera "xyz789"
  → Atacante recibe access_token nuevo

Usuario legítimo intenta renovar sesión:
  POST /auth/refresh { refresh_token: "abc123" }
  → BD: "abc123" existe, REVOCADO
  → 401 Unauthorized
  → Usuario es redirigido al login
```

---

## Revocación en cascada

Cambiar o restablecer la contraseña revoca **todos** los refresh tokens activos del usuario en la BD. Esto cierra todas las sesiones abiertas en todos los dispositivos — si alguien tiene acceso no autorizado a la cuenta, pierde la sesión en el momento en que la contraseña cambia.

```python
# backend/app/routers/privado.py y auth.py
db.query(RefreshToken).filter(
    RefreshToken.id_usuario == usuario.id_usuario,
    RefreshToken.revocado == False
).update({"revocado": True})
```

---

## Tabla `refresh_tokens`

```sql
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario  INT         NOT NULL,
    token       VARCHAR(64) NOT NULL UNIQUE,
    expira_en   DATETIME    NOT NULL,
    revocado    TINYINT(1)  NOT NULL DEFAULT 0,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);
```

`ON DELETE CASCADE`: si se borra un usuario, todos sus refresh tokens se eliminan automáticamente.

El token es una cadena aleatoria de 64 caracteres (`secrets.token_urlsafe(48)`), no un JWT. No necesita llevar payload — la identidad del usuario se obtiene por la FK con la tabla `usuarios`.

---

## Por qué no usar JWT para el refresh token

1. Un JWT caducado no se puede revocar antes de tiempo — con un token opaco en BD, sí.
2. El refresh token no necesita llevar payload (email, rol, etc.) — solo necesita identificar al usuario, lo que se hace a través de la FK en BD.
3. Un token opaco de 64 caracteres aleatorios es más difícil de atacar que un JWT, cuya estructura es predecible.

---

## Contraseñas

Las contraseñas se hashean con **bcrypt** directamente (sin passlib, que tiene problemas de compatibilidad con versiones recientes). El hash incluye el salt integrado — no se necesita columna `salt` en la BD.

Validación en registro: mínimo 8 caracteres, al menos una mayúscula, una minúscula y un número. La validación ocurre en el schema Pydantic con `@field_validator`. Pydantic v2 añade el prefijo `"Value error, "` al mensaje — el frontend lo limpia con `raw.replace(/^Value error,\s*/i, '')`.

---

## Verificación de email

Las cuentas nuevas se crean con `email_verificado = 0`. El login devuelve 403 hasta que el usuario confirme su dirección.

Hay tres contextos donde aparece `email_verificado` y cada uno tiene un comportamiento distinto:

| Contexto | Valor | Motivo |
|----------|-------|--------|
| `POST /admin/usuarios` (código Python) | `0` explícito | Cuenta nueva sin verificar |
| `ALTER TABLE` en migraciones (`install.sh`) | `DEFAULT 1` | Las cuentas existentes antes de la migración ya estaban verificadas manualmente |
| `modelo-fisico.sql` (schema inicial) | `DEFAULT 0` | Instalaciones nuevas: todas las cuentas nuevas empiezan sin verificar |

El endpoint `POST /auth/reset` (restablecer contraseña) activa `email_verificado = 1` si estaba a 0, porque el usuario demostró tener acceso al email al completar el flujo de recuperación.

---

## Envío de correo

Los tres correos que salen de la aplicación —verificación, recuperación de
contraseña y formulario de contacto— comparten una única función,
`_entregar_mensaje()` en `backend/app/auth.py`:

```python
with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as servidor:
    if SMTP_TLS:
        servidor.starttls()
    if SMTP_USER:
        servidor.login(SMTP_USER, SMTP_PASSWORD)
    servidor.send_message(msg)
```

**El cifrado va antes que la autenticación.** Invertir ese orden enviaría la
contraseña del SMTP en claro por la red.

Ambos pasos son condicionales, y ahí está la razón de que el entorno de
desarrollo no necesite configurar nada: Mailpit acepta conexiones sin cifrar y
sin credenciales, así que con los valores por defecto el envío es exactamente
el de siempre. Los proveedores reales (Gmail, Brevo) exigen las dos cosas, y se
activan rellenando `SMTP_TLS` y `SMTP_USER` en `docker/.env`.

El `timeout` no es decorativo: sin él, un servidor SMTP que acepta la conexión
y luego no responde dejaría la petición HTTP colgada indefinidamente.

### Quién parece que envía, y qué dice el pie

El sitio se llama «Subvenciones DGDA», el dominio es `subvencionesdgda.org` y
el asunto de los correos dice lo mismo. Todo suena a organismo oficial, y quien
recibe una verificación puede creer que se la manda la administración que
concede las ayudas. Dos piezas del código lo evitan.

**`_remitente()`** compone la cabecera `From` con nombre visible:

```
Subvenciones DGDA - web independiente <datos.subvencionesdgda@gmail.com>
```

Esto **se lee en la bandeja antes de abrir nada**, así que es donde más gente
ve la aclaración. Y tiene una trampa que cuesta descubrir: **el nombre que se
configure en Gmail no sirve aquí**. Ese solo se aplica a los correos enviados a
mano desde su interfaz; los que manda la aplicación van por SMTP con la
cabecera que pone este código. Se ajusta con `EMAIL_NOMBRE`.

Va en **ASCII puro**, con guion y no con «·», porque un carácter no ASCII
obliga a codificar la cabecera en MIME (`=?utf-8?q?...?=`). Los clientes
modernos lo descodifican, pero en ASCII viaja limpia y se ve igual en todas
partes. Un test lo comprueba.

**`_firma()`** añade el pie a los correos que van a personas de fuera —
verificación y recuperación:

```
—
Subvenciones DGDA · subvencionesdgda.org
Web independiente de análisis de datos públicos. No es un sitio oficial
ni tramita subvenciones: los datos proceden del BDNS y del BOE.
```

Dice **tres cosas y no una**: que es independiente, que no tramita —que es la
confusión concreta que se quiere evitar—, y de dónde salen los datos. Negar sin
explicar qué sí eres deja a medias a quien lo lee.

El correo del formulario de contacto lleva un pie más corto: va a la propia
administradora, así que solo indica de qué sitio procede.

> Estos dos textos tienen que decir lo mismo que el pie de la web y que el
> aviso legal. Si se cambia uno, hay que revisar los otros: son cuatro
> superficies distintas contando lo mismo.

### Los enlaces de los correos

Los correos de verificación y recuperación llevan dentro un enlace a la web, y
su base sale de `SITE_URL`:

```python
SITE_URL = (os.getenv("SITE_URL") or "https://subvencionesDGDA.local").rstrip("/")
enlace   = f"{SITE_URL}/reset-password.html?token={token}"
```

Es el punto de configuración que falla más silenciosamente: si apunta a un
dominio equivocado, el correo se envía y llega, pero el enlace no lleva a
ninguna parte. Como la recuperación por email es la única forma de recobrar el
acceso cuando se olvida la contraseña de administración, conviene **probar el
flujo completo nada más desplegar**.

El `rstrip("/")` evita que un `SITE_URL` acabado en barra genere enlaces con
doble barra.

### Fallos de envío

| Correo | Si el SMTP falla | Por qué |
|---|---|---|
| Verificación y recuperación | Se registra el error y la petición continúa | El alta y la solicitud de recuperación no deben romperse porque el correo no salga; se puede reenviar |
| Formulario de contacto | Propaga el error → HTTP 503 | Fingir que el mensaje se envió dejaría a la persona esperando una respuesta que nunca llegaría |

Los dos primeros capturan `(smtplib.SMTPException, OSError)`. `OSError` es
necesario porque una conexión rechazada o un timeout **no** son `SMTPException`
y, sin él, tumbarían la petición con un error 500.

---

## Alta de usuarios: sin registro público

**No hay auto-registro.** La creación de cuentas es `POST /admin/usuarios`, protegido por rol `admin`: la administradora da de alta a quien quiera y nadie más puede crear cuentas. La versión con registro abierto queda congelada en el tag `v1.0-completo`.

Diferencias respecto al antiguo `POST /auth/registro`:

| | Registro público (retirado) | Alta desde el panel |
|---|---|---|
| Quién puede llamarlo | Cualquiera | Solo rol `admin` |
| Email ya existente | HTTP 201 fingiendo éxito | HTTP 409 con el motivo |
| Rol de la cuenta | Siempre `registrado` | Se elige al crear |
| Honeypot `sitio_web` | Sí | No hace falta |
| Rate limiting en Nginx | Zona `registro`, 5 req/min | Ninguno |

Las dos primeras filas son la misma decisión vista desde dos lados. De cara al exterior, responder 201 aunque el email existiese era una defensa **anti-enumeración**: impedía usar el formulario para averiguar quién tiene cuenta. Detrás del candado de admin esa amenaza desaparece y ocultar el motivo solo serviría para dejar a la administradora sin entender por qué "no se crea" el usuario; por eso ahí sí se devuelve 409.

El honeypot y el rate limiting protegían un formulario abierto a cualquiera. Sin formulario público, sobran los dos.

La cuenta se crea igualmente **sin verificar** y se envía el email de verificación: quien la reciba confirma que la dirección es suya y existe.

### Dar de alta sin que la contraseña viaje por ningún sitio

Al crear la cuenta hay que ponerle una contraseña, y hacérsela llegar a la persona por mensajería o de viva voz es justo donde una contraseña no debería pasar. **No hace falta:**

1. Crear la cuenta con una contraseña **aleatoria** que no se le diga a nadie.
2. Decirle a la persona que entre en la web y pulse **«¿Olvidaste tu contraseña?»**.
3. Recibe el enlace, elige la suya, y **la cuenta queda verificada en el proceso**.

Funciona porque `POST /auth/recuperar` **no exige que la cuenta esté verificada** —solo que exista y esté activa— y `POST /auth/reset` activa `email_verificado` al completarse. Así la contraseña definitiva solo la conoce su dueña, y ni siquiera hace falta pulsar el email de verificación.

Es el motivo por el que se descartó implementar un alta por invitación con su propio enlace de "establece tu contraseña": costaba media jornada y el resultado es el mismo que ya se consigue con el flujo existente.

---

## Sesión activa en login

Si el usuario ya tiene un `access_token` válido en `localStorage`, `login.html` redirige automáticamente a `privado.html` sin mostrar el formulario. Evita la confusión de ver el formulario de login cuando ya estás dentro.

---

## Renovación automática de sesión en el cliente

### El bug original

Las páginas protegidas (`privado.html`, `exclusivo.html`, `admin.html`) verificaban la sesión al cargar con este flujo:

```javascript
// Flujo original — INCOMPLETO
let token = localStorage.getItem('token');
if (!token) {
    token = await intentarRenovarToken();  // renovaba solo si NO había token
    if (!token) { redirigir al login; return; }
}
// Si llegaba aquí con token expirado → API → 401 → login (sin intentar renovar)
const perfil = await fetch('/privado/perfil', { Authorization: Bearer token });
```

El refresh token (30 días) solo se usaba cuando `localStorage` estaba vacío — por ejemplo, tras borrar la caché del navegador. Si el access token existía en `localStorage` pero había caducado (después de 15 minutos), el código lo usaba directamente, recibía 401, y mandaba al usuario al login sin intentar la renovación automática.

**Síntoma:** el usuario se autenticaba, cambiaba de página tras 15 minutos, y era expulsado aunque su refresh token siguiera siendo válido.

### La solución

Se modificó el manejador de 401 en `fetchAutenticado` (`exclusivo.js`, `privado.js`) y en `verificarAcceso` (`admin.js`) para intentar renovar el token antes de redirigir:

```javascript
// Flujo corregido
if (respuesta.status === 401) {
    const nuevoToken = await intentarRenovarToken();
    if (nuevoToken) {
        // Reintentar la petición con el token nuevo
        const reintento = await fetch(ruta, { Authorization: Bearer nuevoToken });
        if (reintento.ok) return reintento.json();  // ✅ sesión restaurada
    }
    // Solo llega aquí si el refresh token también falló (caducado o revocado)
    redirigir al login;
}
```

Se añadió también `intentarRenovarToken()` a `privado.js` y `admin.js` (solo existía en `exclusivo.js`).

### Flujo completo actual

```text
Página carga → ¿hay access_token en localStorage?
    No  → intentarRenovarToken()
              ↓ OK    → continuar con token nuevo
              ↓ fallo → login
    Sí  → llamada a la API
              ↓ 200   → continuar
              ↓ 401   → intentarRenovarToken()
                            ↓ OK    → reintentar llamada → continuar
                            ↓ fallo → login  ← solo aquí si refresh caducó (30 días)
```

Con este flujo, el usuario solo ve el login si lleva 30 días sin entrar, si hizo logout explícito, o si el administrador revocó su sesión (cambio de contraseña, desactivación de cuenta).

---

## Por qué los tokens viven en `localStorage` y no en cookies

Es la pregunta que hace cualquiera que revise esto, así que conviene que la
respuesta esté escrita: **se evaluó y se decidió mantenerlo**, no es un
descuido.

### Lo que se gana con cookies `httpOnly`

Que el token no sea accesible desde JavaScript. Si alguien lograra ejecutar
código en la página —un XSS—, con `localStorage` puede leer el refresh token y
suplantar la sesión durante 30 días; con una cookie `httpOnly`, no.

### Lo que se pierde, y suele olvidarse

**No es una mejora limpia, es un intercambio.** Las cookies viajan solas en
cada petición al dominio, y eso abre la puerta al **CSRF**: una web ajena puede
provocar que el navegador de la usuaria haga una petición autenticada sin que
ella lo sepa. Con `localStorage` ese ataque no existe, porque el token hay que
adjuntarlo a mano en cada llamada.

Migrar bien exige entonces: fijar `SameSite`, revisar la configuración de CORS,
añadir protección CSRF donde haga falta y reescribir los tests de
autenticación. Es tocar la pieza que hoy funciona sin fallos.

### Por qué aquí el riesgo es estrecho

- **No hay registro público.** Las cuentas las crea la administradora, así que
  no hay una masa de sesiones que robar.
- **No hay contenido escrito por usuarios.** Nadie puede introducir texto que
  otra persona vea, que es el camino habitual de un XSS.
- **Los dos scripts externos llevan SRI**, así que un CDN comprometido no
  ejecutaría código alterado.
- **El access token dura 15 minutos**, lo que acota la ventana de uso.

### Cuándo hay que rehacer este razonamiento

Este análisis vale para el proyecto tal como está hoy. Deja de valer si:

1. se reabre el registro público,
2. aparece contenido escrito por usuarios que otros vean,
3. se añade JavaScript de terceros sin SRI, publicidad o widgets,
4. se pasan a manejar datos más sensibles que un email y un alias.

En ese momento el orden recomendado es: **escapar los datos antes de
`innerHTML`** (hay 44 usos sin función de escapado), **añadir
`Content-Security-Policy`** —primero permisiva, luego estricta, lo que obliga a
mover 21 manejadores inline a JavaScript externo— y **por último** migrar a
cookies `httpOnly`. En ese orden: las dos primeras atacan la causa, y sin ellas
las cookies protegen menos de lo que parece.
