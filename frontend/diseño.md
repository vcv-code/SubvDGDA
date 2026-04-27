# Diseño del Frontend

## Proyecto BDNS / DGDA – Subvenciones Bienestar Animal

Este documento recoge la guía visual, los wireframes, los componentes y la estructura base del frontend del proyecto. Sirve como referencia para la implementación en HTML, CSS y JS.

---

## Índice

1. Paleta de colores  
2. Tipografía
3. Logo del proyecto
4. Sistema de espaciado  
5. Componentes base  
6. Wireframes
7. Fuentes de inspiración de diseño
8. Accesibilidad  
9. Estructura del frontend  
10. Referencias

---

## 1. Paleta de colores

> **Nota:** La paleta actual es provisional y puede revisarse durante la maquetación.

![Paleta de colores](./assets/colores.png)

### Colores principales

- **Verde naturaleza (primario)** — `#47C079`  
- **Verde claro (hover / acentos)** — `#52E38E`  
- **Verde suave (fondos)** — `#E8F5E9`

### Colores secundarios

- **Azul institucional** — `#1565C0`  
- **Azul claro** — `#42A5F5`

### Neutros para tablas y UI

- **Gris muy claro** — `#F5F5F5`  
- **Gris medio** — `#E0E0E0`  
- **Gris texto** — `#616161`  
- **Negro suave** — `#212121`

### Estados

- **Concedida** — `#2E7D32`  
- **No beneficiaria** — `#C62828`  
- **Excluida** — `#EF6C00`  
- **Desistida** — `#6A1B9A`

---

## 2. Tipografía

**Inter** (Google Fonts) como fuente principal, con **Segoe UI** como fallback en Windows. Ideal para dashboards y tablas.
![Tipografía](./assets/tipografia.png)

### Jerarquía tipográfica

- **Títulos**: Inter Bold 32–48 px  
- **Subtítulos**: Inter Medium 20–24 px  
- **Texto normal**: Inter Regular 16 px  
- **Tablas**: Inter Regular 14 px  

---

## 3. Logo del proyecto

A continuación se presenta el logotipo provisional utilizado para el proyecto de análisis de subvenciones para protección animal y gestión de colonias felinas. Representa visualmente la misión del sistema: la transparencia institucional y el bienestar animal.

El diseño combina un escudo dividido en dos mitades: la izquierda con un edificio institucional (referencia a la administración pública) y la derecha con las siluetas de un perro y un gato (referencia al bienestar animal). La composición en blanco y negro transmite seriedad y carácter oficial.

![Logo del proyecto](./assets/logo.png)

## Variantes previstas

Aunque este logotipo puede evolucionar durante el desarrollo, se contemplan las siguientes variantes:

- Versión monocromática en negro (principal, la actual)  
- Versión invertida (blanco sobre fondo oscuro)  
- Versión a color (posible mejora futura, con la paleta verde del proyecto)  

## Usos recomendados

- Encabezado (header) de la aplicación web  
- Documentación del proyecto  
- Material de presentación  

## Usos no recomendados

- Reducir el logotipo por debajo de 32px  
- Colocarlo sobre fondos con poco contraste  
- Alterar proporciones o disposición  
- Añadir sombras o efectos no contemplados en el diseño original  

## Área de seguridad

Se recomienda mantener un margen mínimo equivalente al 20% del ancho del escudo alrededor del logotipo para asegurar su correcta legibilidad en cualquier contexto.

---

## 4. Sistema de espaciado

Escala basada en múltiplos de 8:

- 8 px  
- 16 px  
- 24 px  
- 32 px  
- 48 px  

Escala de referencia: **8 / 16 / 24 / 32 / 48 px**

---

## 5. Componentes base

### Botón primario

- Fondo: `#2E7D32`  
- Texto: blanco  
- Radio: 8 px  
- Padding: 16 px 24 px  

### Botón secundario

- Borde: `#2E7D32`  
- Texto: verde  
- Fondo: blanco  

### Input

- Borde: `#E0E0E0`  
- Radio: 6 px  
- Altura: 44 px  

### Select

- Igual que input, con icono ▼  

### Card

- Fondo: blanco  
- Sombra suave  
- Radio: 12 px  
- Padding: 24 px  

### Tabla

- Header gris claro  
- Filas alternas gris muy suave  
- Texto 14 px  

### Barra de navegación

- Fondo blanco  
- Sombra inferior  
- Altura: 80 px  

---

## 6. Wireframes del sistema

Los siguientes wireframes representan la estructura visual inicial del proyecto
según el documento PDF de referencia.

---

### 6.1 Home (Página principal)

Elementos clave:

- Header con navegación superior.  
- Hero principal con título, subtítulo y CTA.  
- Métricas destacadas (solicitudes, importe, convocatorias…).  
- Accesos rápidos a buscador y estadísticas.  
- Sección de convocatorias recientes.  
- Bloque de transparencia con KPIs secundarios.  
- Footer institucional.

![Home](./assets/home.png)  

---

### 6.2 Buscador / Página de solicitudes (Listado + filtros)

Elementos clave:

- Filtros superiores: Año, Tipo, Estado, Buscar.  
- Tabla con columnas:
  - Entidad  
  - Expediente  
  - Tipo (EPA / EELL)  
  - Estado (concedida, excluida, desistida…)  
  - Importe  
- Paginación inferior.  
- Diseño orientado a lectura rápida y comparación.

![Página Filtros](./assets/pagFiltros.png)

---

### 6.3 Estadísticas (Dashboard)

Elementos clave:

- Filtros superiores: Tipo y Año.  
- KPIs agregados:
  - Convocatorias  
  - EPA totales  
  - EELL totales  
  - Excluidas  
  - Desistidas  
- Gráficos:
  - Barras: importe concedido por año.  
  - Barras comparativas: EPA vs EELL.  
  - Tarta: reparto por estado.  
  - Líneas: evolución anual.  
- Estructura tipo dashboard, clara y analítica.

![Estadísticas](./assets/estadisticas.png)

---

### 6.4 Login / Registro

Elementos clave:

- Formulario centrado.  
- Campos:
  - Email  
  - Contraseña  
- Botón “Entrar”.  
- Enlace “Crear cuenta”.  
- Estética minimalista y coherente con el resto del sistema.

![Login](./assets/login.png)
![Registro](./assets/registro.png)

> **Nota:** Los wireframes incluyen botones de acceso con Google y GitHub. Esta funcionalidad (OAuth) no está implementada en el backend actual y se reserva como **mejora futura**. La implementación real usa únicamente email y contraseña.

---

### 6.5 Perfil de usuario

Parte de `privado.html` (requiere sesión iniciada). Ver también sección 6.7 para el contenido exclusivo de la zona privada.

Elementos clave:

- Datos básicos del usuario (email, rol).  
- Botones:
  - Cambiar contraseña *(pendiente de implementar en el backend)*  
  - Cerrar sesión  

---

### 6.6 Páginas de error

Páginas visuales para los errores HTTP que el backend ya gestiona: 401 (no autenticado), 403 (sin permisos), 404 (no encontrado), 422 (datos inválidos) y 500 (error interno). El backend devuelve JSON estructurado con `error`, `mensaje` y `sugerencia`; el frontend mostrará esos campos de forma visual.

Elementos clave:

- Mensaje claro y centrado.  
- Botones de acción:
  - Volver al inicio  
  - Reintentar (en 500)  
- Diseño simple y accesible.  

---

### 6.7 Zona privada

Página `privado.html`, accesible solo con sesión iniciada (token JWT válido). Agrupa el perfil de usuario (6.5) y el resumen exclusivo. Corresponde a las rutas `/privado/perfil` y `/privado/resumen-exclusivo` del backend.

Elementos clave:

- Datos del usuario autenticado (email, rol).  
- Resumen exclusivo: KPIs restringidos (importe total concedido, nº de beneficiarios únicos, convocatorias activas).  
- Botón "Cerrar sesión".  
- Redirección automática a login si el token es inválido o ha expirado.

---

### 6.8 Referencia visual

Los wireframes completos se encuentran en el documento PDF original:

**`/frontend/assets/wireframes_subvenciones_bienestar_animal.pdf`**

---

##  7. Fuentes de inspiración de diseño

El diseño del frontend se ha desarrollado tomando como referencia plataformas y organizaciones que destacan por su claridad visual, accesibilidad y capacidad para presentar grandes volúmenes de datos de forma comprensible. Estas fuentes no se han utilizado para replicar interfaces, sino para identificar patrones de diseño efectivos y buenas prácticas aplicables al proyecto.

### 1. Datos.gob.es  

https://datos.gob.es/  

Referencias:

- Jerarquía visual institucional  
- Presentación clara de datos públicos  
- Navegación accesible  

### 2. PACMA  

https://pacma.es/  

Referencias:

- Tono comunicativo directo  
- Uso de imágenes relacionadas con bienestar animal  

### 3. WWF España  

https://www.wwf.es/ 

Referencias:

- Presentación de métricas  
- Bloques visuales informativos  
- Equilibrio entre texto e imagen  

### 4. Booking.com  

https://www.booking.com/  

Referencias:

- Diseño de filtros avanzados  
- Tablas con resultados  
- Patrones de interacción intuitivos  

### 5. Normativas y estándares

- WCAG 2.1  
- BOE / BDNS / DGDA  

---

## 8. Accesibilidad

Cumplimiento WCAG 2.1 AA:

- Contraste mínimo 4.5:1  
- Tipografía legible  
- Tamaños escalables  
- Navegación por teclado  
- Etiquetas ARIA  

---

## 9. Estructura del frontend

frontend/
├── css/
│
├── js/
│  
├── assets/
│   ├── img.png
│   ├── wireframes_subvenciones_bienestar_animal.pdf
│  
├── index.html
├── estadisticas.html
├── solicitudes.html
├── login.html
├── privado.html
└── diseño.md

---

## 10. Referencias

### Fuentes de datos y documentación

- **Datos.gob.es** — Portal oficial de datos abiertos en España  
  https://datos.gob.es/

- **DGDA – Dirección General de Derechos de los Animales**  
  Información sobre convocatorias y normativa relacionada.

- **BDNS – Base de Datos Nacional de Subvenciones**  
  Consulta de subvenciones públicas en España.

### Referencias temáticas (bienestar animal)

- **PACMA** — https://pacma.es/  
- **WWF España** — https://www.wwf.es/

### Referencias de diseño / benchmarking

- **Booking.com** — https://www.booking.com/

### Normativas y estándares

- **WCAG 2.1**  
- **BOE**
