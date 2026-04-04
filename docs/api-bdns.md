# API BDNS – Análisis inicial

## Descripción

La Base de Datos Nacional de Subvenciones (BDNS) proporciona una API pública que permite consultar información sobre convocatorias y concesiones de subvenciones públicas.

Documentación oficial:

https://www.infosubvenciones.es/bdnstrans/doc

---

## Endpoints analizados

### Convocatorias

Endpoint utilizado:

```
/convocatorias/busqueda
```

Permite consultar convocatorias de subvenciones registradas en la BDNS.

Ejemplo de información obtenida:

- id
- numeroConvocatoria
- descripcion
- fechaRecepcion
- nivel1
- nivel2
- nivel3

Estos campos permiten identificar la convocatoria y el organismo responsable.

---

### Concesiones

Endpoint analizado:

```
/concesiones/busqueda
```

Este endpoint devuelve información sobre beneficiarios e importes concedidos.

Campos relevantes:

- id
- codConcesion
- fechaConcesion
- beneficiario
- importe
- numeroConvocatoria
- nivel1
- nivel2
- nivel3

---

## Problema detectado

Las concesiones correspondientes a subvenciones gestionadas por la Dirección General de Derechos de los Animales no aparecen en el endpoint de concesiones de la API BDNS.

Los datos de beneficiarios, importes y estados de las solicitudes solo están disponibles en las resoluciones oficiales publicadas por la DGDA.

---

## Fuentes alternativas utilizadas para las resoluciones

Ante la ausencia de estos datos en la API, se analizaron dos tipos de documentos oficiales publicados por la DGDA y el BOE:

### Documentos PDF

Las resoluciones de convocatorias EPA (2021–2024) y EELL (2023–2024) se publican en formato PDF. Se desarrollaron parsers específicos con `pdfplumber` para extraer las tablas de beneficiarios, importes y estados de cada convocatoria.

Sin embargo, el formato PDF presentó limitaciones importantes en algunos casos:

- Tablas con diseños complejos y saltos de página que dificultan la extracción automática.
- En la convocatoria EELL 2025, parte de la información (listado de beneficiarias) se publicó como **imágenes escaneadas dentro del PDF**, lo que impidió la extracción automática de texto. Ese listado tuvo que reconstruirse manualmente a partir de las imágenes del BOE.

### Documentos XML del BOE

Como alternativa más fiable, se utilizaron los **archivos XML estructurados** publicados por el BOE para las convocatorias EPA (2021–2025) y EELL (2025). Estos documentos contienen la misma información que los PDFs pero en formato estructurado, lo que facilita la extracción automática y elimina los problemas de parseo de tablas.

Se desarrollaron parsers específicos con `BeautifulSoup` para procesar estos XML y extraer los datos necesarios.

---

## Conclusión

Para obtener la información completa del proyecto se combinan tres fuentes:

- **API BDNS** — datos de convocatorias (identificadores, fechas, descripciones)
- **XML del BOE** — resoluciones de concesiones EPA (2021–2025) y EELL 2025, fuente principal por su estructura fiable
- **PDF de resoluciones** — resoluciones EELL 2023 y 2024, donde no existe XML disponible

Esta combinación permite construir el dataset unificado con los 6398 registros del proyecto.
