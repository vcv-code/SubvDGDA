# Modelo de datos del sistema

## 1. Introducción

El modelo de datos del sistema se ha diseñado a partir de la integración de dos fuentes principales:

- La API de la Base de Datos Nacional de Subvenciones (BDNS), que proporciona información estructurada sobre convocatorias.
- Los documentos oficiales publicados por la Dirección General de los Derechos de los Animales (DGDA), que contienen información sobre concesiones y exclusiones.

Tras el proceso de extracción, limpieza y unificación, se obtiene un **dataset final consolidado** que combina la información de convocatorias con los datos de concesiones publicados en los documentos oficiales.

El objetivo del modelo es proporcionar una estructura clara, simple y eficiente para almacenar y consultar la información final del sistema.

---

## 2. Fuentes de datos utilizadas

### 2.1 API BDNS

La API BDNS permite obtener información sobre convocatorias públicas, incluyendo:

- código BDNS  
- descripción  
- organismo convocante  
- fecha de publicación  
- año  

Esta información se utiliza para construir la tabla **convocatorias**, que actúa como referencia para las concesiones.

### 2.2 Documentos oficiales (PDF)

Los documentos PDF publicados por la DGDA contienen:

- listados de concesiones  
- importes concedidos  
- puntuaciones  
- entidades beneficiarias  
- causas de exclusión (solo en EELL 2025)  
- tramos (solo en EELL 2025)  

Estos datos se procesan mediante parsers específicos y se integran en la tabla **concesiones**.

---

## 3. Proceso de transformación

El pipeline del proyecto realiza:

1. Extracción de datos desde BDNS y PDF.  
2. Limpieza y normalización.  
3. Unificación en un dataset final (`dataset_unificado.json`).  
4. Generación del modelo de datos relacional.

El resultado es un modelo simplificado, centrado en las entidades realmente presentes en los datos finales.

---

## 4. Entidades del modelo de datos

Tras analizar las fuentes y el dataset final, se identifican únicamente **dos entidades reales** necesarias para la base de datos:

- **convocatorias**  
- **concesiones**

Otras entidades que aparecen en los documentos administrativos (solicitudes, beneficiarios, agrupaciones, causas, líneas de actuación…) **no se implementan** porque no existen como datos estructurados en el dataset final o no son necesarias para los objetivos del proyecto.

---

## 4.1 Convocatorias

Representa cada convocatoria oficial obtenida desde la API BDNS.

**Campos principales:**

- `id_convocatoria` (PK)  
- `codigo_bdns`  
- `descripcion`  
- `organismo`  
- `fecha_publicacion`  
- `anio`  

Esta tabla sirve como referencia para vincular las concesiones con su convocatoria correspondiente.

---

## 4.2 Concesiones

Contiene la información final unificada de todas las concesiones publicadas por la DGDA.

**Campos principales:**

- `id` (PK, autoincremental)  
- `anio`  
- `tipo` (EPA / EELL)  
- `num_expediente`  
- `entidad`  
- `cif`  
- `puntuacion`  
- `importe`  
- `estado`  
- `tramo` (solo EELL 2025)  
- `causa_exclusion` (solo excluidas EELL 2025)  
- `codigo_bdns` (FK lógica hacia convocatorias)

Esta tabla es el núcleo del sistema y contiene todos los datos necesarios para análisis y visualizaciones.

---

## 5. Relaciones del modelo

### Convocatorias 1 ─── N Concesiones

Una convocatoria puede tener múltiples concesiones asociadas.

La relación se establece mediante el campo `codigo_bdns` y el año de la convocatoria.

No existen más relaciones en el modelo físico, ya que el dataset final no contiene información estructurada sobre solicitudes, beneficiarios, agrupaciones o causas como entidades independientes.

---

## 6. Decisiones de diseño

### 6.1 Modelo simplificado

Aunque los documentos administrativos mencionan conceptos como:

- solicitudes  
- beneficiarios  
- agrupaciones  
- miembros  
- causas de exclusión  
- líneas de actuación  

estos elementos **no existen como datos estructurados** en el dataset final y no pueden modelarse como tablas independientes.

Por ello, el modelo se simplifica a:

- convocatorias  
- concesiones  

### 6.2 Campos específicos de EELL 2025

Los campos `tramo` y `causa_exclusion` solo aparecen en EELL 2025.  
Se incluyen como campos opcionales dentro de la tabla concesiones.

### 6.3 EPA 2025 no integrable

Los datos de EPA 2025 no pueden integrarse porque:

- no existe un listado oficial de concesiones  
- solo se publican solicitudes  
- no hay resolución definitiva  

Por tanto, EPA 2025 queda fuera del modelo.

---

## 7. Diagrama entidad–relación

El siguiente diagrama representa el modelo final del sistema, tras la revisión del dataset unificado y la eliminación de entidades conceptuales no implementadas.

![Diagrama entidad-relación del modelo de datos](img/modelo-datos-er.png)

> **Nota:** Las entidades marcadas con (*) en el diagrama corresponden a elementos conceptuales del proceso administrativo, pero no se implementan en la base de datos.

---

## 8. Herramientas utilizadas

- **diagrams.net (draw.io)** para el diseño del diagrama ER.  
- **Python + parsers propios** para la extracción y limpieza de datos.  
- **JSON** como formato intermedio de almacenamiento.  
- **MySQL Workbench** (opcional) para la futura implementación física del modelo.

---

## 9. Conclusión

El modelo de datos final es simple, eficiente y totalmente alineado con el dataset unificado del proyecto.  
Permite realizar análisis, visualizaciones y consultas sin introducir complejidad innecesaria ni tablas que no existen en las fuentes reales.

