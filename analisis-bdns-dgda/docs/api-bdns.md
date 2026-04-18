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

Sin embargo, los beneficiarios sí aparecen en las resoluciones oficiales publicadas en formato PDF.

---

## Conclusión

Para obtener la información completa será necesario combinar:

- datos de la API BDNS
- extracción de información desde los PDFs de resolución