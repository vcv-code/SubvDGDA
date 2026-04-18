# Análisis BDNS – Subvenciones de Animales  
### *Trabajo de Fin de Grado – Desarrollo Frontend + Integración Backend*

Este proyecto forma parte del **Trabajo de Fin de Grado (TFG)** y tiene como objetivo desarrollar una aplicación web que permita **analizar, visualizar y explorar subvenciones relacionadas con animales**, utilizando datos procedentes de la **BDNS (Base de Datos Nacional de Subvenciones)**.

El desarrollo combina **React (JSX), HTML, CSS y JavaScript moderno**, junto con la integración hacia un **backend propio**, encargado de procesar, filtrar y exponer los datos necesarios.

---

## 🚀 Estado del Proyecto

Actualmente se encuentra en desarrollo activo.

### Avances completados:
- ✔️ **Página Home**: estructura base, diseño inicial y primeros componentes funcionales  
- ✔️ **Integración inicial con backend** para obtener datos reales o mockeados  
- ✔️ **Arquitectura de componentes en React** para escalar el proyecto  
- ✔️ **Estilos base en CSS** y estructura responsive inicial  

### Pendiente:
- ⏳ Desarrollo de páginas adicionales (Buscador, Detalle, Estadísticas, etc.)  
- ⏳ Refinar la comunicación frontend–backend  
- ⏳ Mejorar accesibilidad, rendimiento y diseño final  
- ⏳ Documentación técnica ampliada  

---

## 🧩 Tecnologías Utilizadas

### Frontend
- **React + JSX** – componentes reutilizables, estado, renderizado eficiente  
- **HTML5** – estructura semántica  
- **CSS3** – estilos, layout, responsive  
- **JavaScript ES6+** – interacción, eventos, lógica  

### Backend
- API propia (tecnología a definir según el TFG)  
- Endpoints para consulta de subvenciones  
- Procesamiento y filtrado de datos BDNS  

### Control de versiones
- **Git + GitHub**  
- Flujo de trabajo basado en ramas (`main`, `dev`, `feature/...`)  

---

## ⚛️ ¿Por qué React?

React se utiliza en este proyecto por varias razones técnicas y académicas que lo convierten en una elección sólida frente a alternativas como Vue, Angular o desarrollo sin framework.

### **1. Componentes reutilizables**
React permite dividir la interfaz en **componentes independientes**, fáciles de mantener y escalar.  
Esto es clave en un proyecto con múltiples páginas como:

- Home  
- Buscador  
- Detalle  
- Estadísticas  

Cada parte puede construirse como un módulo reutilizable.

### **2. JSX: escribir HTML dentro de JavaScript**
JSX facilita:

- lógica + interfaz en un mismo archivo  
- renderizado dinámico  
- lectura más clara del flujo de datos  

Esto acelera el desarrollo y reduce errores.

### **3. Virtual DOM = rendimiento**
React actualiza solo lo necesario en pantalla, lo que mejora:

- velocidad  
- eficiencia  
- experiencia de usuario  

Especialmente útil cuando se renderizan **tablas, filtros o listados de subvenciones**.

### **4. Ecosistema maduro**
React tiene:

- documentación extensa  
- comunidad enorme  
- librerías para gráficos, tablas, routing, etc.  

Ideal para un TFG donde necesitas justificar decisiones técnicas.

### **5. Escalabilidad**
React permite empezar con algo pequeño (como tu Home) y crecer hacia:

- routing  
- estado global  
- dashboards  
- visualizaciones  

Sin reescribir la base.

---

## 🏗️ Arquitectura del Proyecto

/analisis-bdns-dgda
│
├── /frontend
│   ├── index.html
│   ├── /css
│   │   └── styles.css
│   ├── /components
│   │   └── Home.jsx
│   └── /assets
│
├── /backend
│   ├── server.js / app.py / index.php (según tecnología)
│   ├── /routes
│   └── /controllers
│
└── README.md

---

## 🐾 Objetivo del Proyecto

El propósito principal es ofrecer una herramienta que permita:

- Consultar subvenciones relacionadas con animales  
- Visualizar datos de forma clara y accesible  
- Facilitar análisis comparativos y filtrados  
- Presentar información relevante para ciudadanos, asociaciones o administraciones  

---

## 🖥️ Página Home (estado actual)

La página Home ya implementa:

- ✔️ Layout principal  
- ✔️ Componentes JSX iniciales  
- ✔️ Estilos base  
- ✔️ Conexión inicial con backend  
- ✔️ Render dinámico de datos  

Próximas mejoras:

- ⏳ Tarjetas informativas  
- ⏳ Gráficos o visualizaciones  
- ⏳ Accesos rápidos a otras secciones  
- ⏳ Diseño final y refinado  

---

## 📅 Páginas Futuras

El proyecto incluirá:

- Buscador avanzado

- Detalle de subvención

- Panel de estadísticas

- Comparador

- Sistema de filtros dinámicos