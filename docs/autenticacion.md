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
