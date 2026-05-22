# Manual de usuario

## Plataforma de análisis de subvenciones de bienestar animal

**Versión:** 1.0 — Mayo 2026

---

## ¿Qué es esta plataforma?

Esta plataforma permite consultar y analizar las subvenciones públicas de bienestar animal que el Gobierno de España ha convocado entre 2021 y 2025. Hay dos tipos de subvenciones:

- **EPA (Entidades de Protección Animal):** para protectoras y asociaciones sin ánimo de lucro dedicadas al cuidado de animales.
- **EELL (Entidades Locales):** para ayuntamientos, mancomunidades y otras entidades locales para el control de colonias felinas y animales abandonados.

La mayoría de las funciones están disponibles **sin necesidad de registrarse**. El registro solo es necesario para acceder al contenido exclusivo (tabla detallada y mapa de distribución geográfica).

---

## Acceso a la plataforma

Abre el navegador y ve a:

- `https://subvencionesDGDA.local` (si el dominio está configurado en tu máquina)
- `http://localhost` (alternativa sin HTTPS)

Si el navegador muestra un aviso de "Conexión no segura" o "No es privada", es normal: el certificado es autofirmado para el entorno local. Haz clic en **Avanzado** → **Continuar a subvencionesDGDA.local** (o equivalente en tu navegador) para acceder.

---

## Página de inicio

La página de inicio muestra un resumen de la plataforma con:

- **Métricas principales:** número total de solicitudes, importes concedidos y años cubiertos.
- **Gráficas de evolución:** evolución anual del importe total concedido y número de solicitudes por tipo (EPA y EELL).
- **Avisos de convocatorias activas:** si hay una convocatoria del año en curso sin resolución publicada, aparece un aviso informativo.
- **Tarjetas de convocatorias recientes:** acceso directo a las últimas convocatorias.

Cada gráfica tiene un botón de información (ⓘ) que abre un modal con conclusiones y análisis del dato representado.

---

## Buscador de solicitudes

El buscador (`/buscador.html`) permite consultar todas las solicitudes de subvenciones con distintos filtros.

### Filtros disponibles

| Filtro | Descripción |
|--------|-------------|
| **Tipo** | EPA (protectoras) o EELL (entidades locales) |
| **Año** | De 2021 a 2025 |
| **Estado** | Concedida, No beneficiaria, Excluida, Desistida |
| **CCAA** | Comunidad autónoma (solo para EELL) |
| **Búsqueda libre** | Nombre de la entidad o número de expediente |
| **Ordenación** | Por nombre, importe o año |

### Cómo buscar

1. Selecciona los filtros que quieras aplicar en el panel lateral o superior.
2. La tabla se actualiza automáticamente con los resultados.
3. La URL del navegador se actualiza con los filtros aplicados — puedes guardarla o compartirla para reproducir la misma búsqueda.

### Paginación

Los resultados se muestran de 50 en 50. Usa los botones de paginación en la parte inferior para navegar entre páginas.

### Exportar a CSV

El botón **Exportar CSV** descarga todos los resultados del filtro actual (hasta 5.000 registros) en formato CSV. Si el resultado tiene más de 5.000 registros, se mostrará un mensaje indicando que debes aplicar más filtros para acotar la búsqueda.

### Ficha de entidad

Haz clic en el nombre de cualquier entidad para abrir un panel lateral con su historial de solicitudes, importe acumulado y evolución por convocatoria, sin salir del buscador. En el pie del panel encontrarás el enlace **Ver página completa →** que abre la ficha en una página independiente, con una URL que puedes guardar o compartir.

---

## Estadísticas

Hay dos páginas de estadísticas, accesibles desde el menú de navegación:

### EPAs — Entidades de Protección Animal

Incluye análisis sobre:

- Evolución del importe total concedido por año
- Distribución del importe por rangos
- Importes medios y medianos por convocatoria
- Nuevas entidades vs entidades recurrentes
- Top 10 de entidades beneficiarias por importe acumulado

### EELL — Entidades Locales

Incluye análisis sobre:

- Evolución por año
- Ranking de CCAA y provincias por importe concedido
- Concentración del importe (qué porcentaje reciben las 10 principales entidades)
- Top de municipios por importe

En ambas páginas, cada gráfica tiene un botón ⓘ que abre un modal con las conclusiones del análisis.

---

## Registro e inicio de sesión

### Crear una cuenta

1. Haz clic en **Acceder** en la barra de navegación.
2. En la página de login, haz clic en **¿No tienes cuenta? Regístrate**.
3. Introduce tu email y una contraseña que cumpla los requisitos (mínimo 8 caracteres, al menos una mayúscula, una minúscula y un número).
4. Recibirás un email de verificación. Haz clic en el enlace del email para activar tu cuenta.

> **Nota:** Si el email no llega, comprueba la carpeta de spam o usa la opción "Reenviar email de verificación" en la página de login.

### Iniciar sesión

1. Ve a la página de inicio de sesión haciendo clic en **Acceder**.
2. Introduce tu email y contraseña.
3. Si ya tienes sesión iniciada, serás redirigida automáticamente a tu perfil.

### Cerrar sesión

Haz clic en **Cerrar sesión** en la barra de navegación (visible una vez iniciada la sesión).

---

## Zona privada — Mi perfil

Una vez registrada y con sesión iniciada, accede a tu perfil desde el enlace **Mi perfil** en la barra de navegación.

### Cambiar nombre o alias

Puedes establecer un nombre o alias que se mostrará en el panel. Introduce el nombre deseado y haz clic en **Guardar**.

### Cambiar contraseña

1. Introduce tu contraseña actual.
2. Introduce la nueva contraseña (mismos requisitos que en el registro).
3. Confírmala y haz clic en **Cambiar contraseña**.

Al cambiar la contraseña, todas las sesiones activas en otros dispositivos se cerrarán automáticamente.

### Recuperar contraseña

Si no recuerdas tu contraseña:

1. Ve a la página de login y haz clic en **¿Olvidaste tu contraseña?**
2. Introduce tu email y haz clic en **Enviar enlace**.
3. Recibirás un email con un enlace de recuperación válido durante 15 minutos.
4. Haz clic en el enlace e introduce tu nueva contraseña.

---

## Contenido exclusivo

El contenido exclusivo está disponible para todos los usuarios registrados. Accede desde **Exclusivo** en la barra de navegación o desde el botón preparado para ello que encontrará en el perfil.

### Tabla de resumen por convocatoria

Muestra un resumen completo de todas las convocatorias (EPA y EELL) con el total de solicitudes, concedidas, no beneficiarias, excluidas, desistidas e importe total concedido por año.

Las filas con la etiqueta *"Resolución pendiente de publicación"* corresponden a convocatorias del año en curso cuya resolución aún no ha sido publicada en el BOE.

### Mapa de calor por CCAA

El mapa muestra el importe total concedido a entidades locales por comunidad autónoma (datos de 2023 a 2025). Los colores más oscuros indican mayores importes.

**En ordenador:**

- Pasa el cursor por encima de una comunidad para ver el importe total y el número de concesiones.
- Haz clic en una comunidad para ver el top de municipios beneficiarios (acumulado total y último año disponible).

**En móvil o tablet:**

- Un toque muestra el nombre de la comunidad y su importe en el centro del mapa.
- Doble toque abre el modal con el top de municipios.

Las comunidades en rojo no tienen concesiones de este tipo de subvención registradas en el periodo analizado.

---

## Panel de administración

El panel de administración solo está disponible para usuarios con rol de administrador. Desde `admin.html` se puede:

- Ver el estado general del sistema (número de solicitudes, usuarios, convocatorias).
- Gestionar usuarios: cambiar roles (registrado / admin) y activar o desactivar cuentas.
- Gestionar avisos: activar, desactivar o eliminar los avisos de convocatorias pendientes que aparecen en la home.
- Consultar los logs de acceso y errores del servidor.

### Credenciales de demo

Para acceder al panel en una instalación nueva:

- **Email:** admin@demo.com
- **Contraseña:** Admin1234!

Se recomienda cambiar estas credenciales si se va a usar en un entorno real.

---

## Recursos

La página **Recursos** (`/recursos.html`) ofrece un directorio de organizaciones de protección animal, tanto genéricas como especializadas, y campañas activas. Esta sección está disponible para todos los usuarios sin necesidad de registro.

---

## Páginas de error

- **404 — Página no encontrada:** si accedes a una URL que no existe, verás una página con un mensaje amigable y un botón para volver al inicio.
- **50x — Error del servidor:** si el servidor tiene algún problema técnico, verás una página informativa amigable con un botón de "Reintentar". Esta página se muestra aunque el servidor backend esté temporalmente caído.

---

## Preguntas frecuentes

**¿La información está actualizada?**
Los datos cubren las convocatorias resueltas entre 2021 y 2025. Para la convocatoria del año en curso, el sistema comprueba periódicamente si se ha publicado en la BDNS y muestra un aviso en la página de inicio. Cuando se publica la resolución, el aviso desaparece automáticamente. Los datos detallados de cada resolución (beneficiarios e importes) se añaden manualmente por el equipo de desarrollo en cuanto están disponibles en el BOE.

**¿Puedo descargar todos los datos?**
Sí, desde el buscador puedes exportar a CSV los resultados de cualquier consulta con filtros (hasta 5.000 registros por exportación).

**¿Mis datos están seguros?**
La plataforma usa HTTPS y almacena las contraseñas con cifrado bcrypt. Los tokens de sesión tienen una duración limitada (15 minutos para el token de acceso, 30 días para el de renovación automática).

**¿Por qué el mapa solo muestra EELL y no EPA?**
Las protectoras (EPA) son asociaciones privadas cuya ubicación no es directamente derivable de su CIF. Las entidades locales sí tienen el código de provincia codificado en el NIF, lo que permite asignarlas a su comunidad autónoma.

**¿Por qué algunos años aparecen en el mapa con menos comunidades?**
El primer año de datos EELL es 2023. Las convocatorias anteriores a ese año solo incluyen EPA, por lo que el mapa de EELL no tiene datos de 2021 ni 2022.
