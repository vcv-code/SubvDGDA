# EELL 2024 — ficheros de origen

| Fichero | Qué es |
|---|---|
| `resolucion-def-EELL2024.pdf` | Resolución **definitiva**. Es la que carga el pipeline. |
| `propuesta-provisional-EELL2024.pdf` | **Propuesta provisional de concesión**, 9 de octubre de 2024. |

## Qué fase es exactamente

En 2024 hay **dos** documentos con nombre parecido, y este es el segundo:

1. *Lista definitiva de admitidas y excluidas + propuesta de resolución
   provisional* — 19 de septiembre de 2024, con plazo de alegaciones hasta el 3
   de octubre. **No se conserva.**
2. *Resolución por la que se aprueba la propuesta provisional de concesión* —
   9 de octubre de 2024. **Es este fichero.**

Hubo además una *corrección de errores* de la lista definitiva entre medias,
que tampoco se conserva.

Conviene no fiarse del nombre del fichero: en 2023 ambas fases van en el mismo
PDF y en 2025 se llaman de otra manera. El mapa está en `../README.md`.

## Ojo: la provisional de 2024 NO tiene texto extraíble

Va como imagen. `mutool draw -F txt` saca unas 890 palabras, que son solo los
membretes y el pie de firma: ni los antecedentes ni los anexos.

Para comparar provisional y definitiva de este año haría falta pasarle un OCR
—`ocrmypdf` o similar—, y eso es trabajo aparte. Se guarda igualmente porque el
documento solo vive en el portal del Ministerio mientras la convocatoria está
abierta, y después no hay forma de recuperarlo.

La de 2025 sí se lee, y de ella sale la comparación que está anotada en
`../2025/README.md`.
