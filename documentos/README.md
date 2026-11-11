# Documentos para presentar a ayuntamientos

Fuente de los PDF que publica la web en `frontend/assets/docs/`. Lo que se
edita es el **HTML de esta carpeta**; el PDF es una salida, no un original. Si
alguien edita el PDF directamente, el siguiente reimpreso se lo come.

## Qué hay aquí

| Fichero | Qué es | ¿Se publica? |
|---|---|---|
| `nota-pienso-colonias.html` | Nota informativa genérica, para cualquier municipio | **Sí** → `frontend/assets/docs/nota-compra-publica-pienso-colonias.pdf` |
| `nota-pienso-colonias.md` | La misma nota en Markdown, para reutilizar el texto | No (solo repo) |

Hubo un `.docx`, hecho para editar la nota en Word. Se abandonó esa vía —Word
rompía el formato y el PDF que salía no tenía capa de texto— y se **borró el
11-11-2026**, porque ya no reflejaba los cambios y contradecía al HTML.
| `nota-pienso-fuenlabrada.html` | Versión adaptada a un municipio, con datos reales | **No** — ignorada en git, ver abajo |

La nota genérica lleva huecos `<span class="hueco">[ciudad]</span>` pensados
para que cada entidad la complete con los suyos.

### Por qué la de Fuenlabrada no se versiona

Está en `.gitignore`. Lleva las cuentas de la asociación (gasto anual, importe
justificado con factura, subvenciones recibidas) y describe la situación de las
otras dos entidades que trabajan en el municipio, que no han autorizado nada.
Además es un documento de negociación para una reunión, no divulgativo. Mismo
criterio que `docs/privado/`: no debe publicarse aunque el repositorio sea
público.

Si algún día interesa publicar un ejemplo resuelto, hay que hacer una **versión
anonimizada**: mismo método y cifras redondeadas, sin nombrar municipio ni
caracterizar a terceros.

## Cómo se genera el PDF

1. Abrir el `.html` en **Chrome** y pulsar `Ctrl+P`.
2. Destino: **«Guardar como PDF»** (el de Chrome).
3. Más ajustes → **desmarcar «Encabezados y pies de página»**.
4. Márgenes predeterminados, escala 100 %.
5. Copiar el PDF a `frontend/assets/docs/` con el nombre que espera
   `frontend/recursos.html`.

> **No usar el driver «Adobe PDF».** Pierde la tabla ToUnicode y el texto se
> extrae como `(cid:NN)`: no se puede copiar ni buscar. El PDF bueno lleva
> `Producer: Skia/PDF`; el malo, `Acrobat Distiller` + `PScript5.dll`.

Los dos HTML son **autocontenidos** (CSS en línea, sin imágenes), así que se
pueden copiar sueltos a cualquier sitio y siguen funcionando.

## De dónde sale cada cifra

Esto está aquí para no tener que volver a deducirlo. Verificado el 11-11-2026.

### Comprobado contra la fuente original

| Dato | Fuente |
|---|---|
| Competencia municipal sobre gatos comunitarios | Ley 7/2023, art. 39.1 |
| Microchip «bajo la titularidad de la Administración local» | Ley 7/2023, art. 38.2 |
| «Gestión» incluye **alimentar** | Ley 7/2023, art. 3.w) (definición) |
| Criterios de alimentación en protocolos autonómicos | Ley 7/2023, art. 40.c) |
| Siguen protegidos como animales de compañía | Ley 7/2023, art. 38.1 |
| Garantizar «acceso a bebida y alimentación» | Ley 7/2023, art. 28.d) |
| Ordenanza debe recoger **derechos** de las cuidadoras | Ley 7/2023, art. 39.1.a) |
| «Entidad colaboradora» (tipo GCOF) | Ley 7/2023, art. 47 |
| Voluntariado «sin contraprestación», gastos reembolsables | Ley 45/2015, arts. 3.1.c y 10.f |
| Reembolso a cargo de **la entidad**, no de la Administración | Ley 45/2015, art. 10.f |
| Supuestos que NO son voluntariado | Ley 45/2015, art. 3.3 |
| Entidades locales promoverán el voluntariado | Ley 45/2015, art. 19 |
| Necesidad determinada «con precisión» | LCSP 9/2017, art. 28.1 |
| Presupuesto adecuado a precios de mercado | LCSP 9/2017, art. 100.2 |
| Mejor relación calidad-precio | LCSP 9/2017, art. 145.1 |
| Precio como único criterio en **suministros** | LCSP 9/2017, art. **145.3.f)** |
| Ofertas anormalmente bajas | LCSP 9/2017, art. 149 |
| Pienso al **10 %** de IVA | Ley 37/1992, art. 91.Uno.1.1º |

> **Ojo con el 145.3:** la letra **f)** es suministros y la **g)** es servicios.
> Se citó la g) por error y se corrigió. Es el tipo de fallo que un técnico de
> contratación ve de inmediato.

### Precios del pienso

Banda de la nota: **1,80 – 2,70 €/kg sin IVA** (≈ 2 – 3 € con IVA del 10 %).

| Marca | €/kg c/IVA | Saco | €/saco | €/kg s/IVA |
|---|---|---|---|---|
| Nutralgape | 2,00 € | 20 kg | 40,00 € | 1,82 € |
| Feral | 2,50 € | 15 kg | 37,50 € | 2,27 € |
| Lobo Azul (CAT 15 kg, a volumen) | 2,61 € | 15 kg | ~39 € | 2,37 € |

Las tres entran en la banda. **No se nombran marcas en la nota**: sugerir
proveedores a un órgano de contratación antes de que licite puede contaminar el
expediente.

El 4 €/kg de la primera versión era precio de tienda, no de contrato: en la
tarifa de Lobo Azul esa cifra corresponde a la línea Grant Free en saco de 6 kg
(3,5–4,2 €/kg sin IVA), que no es lo que licita un ayuntamiento.

### Cálculos derivados

- **Consumo:** 18–22 kg/gato/año = **50–60 g/día**. Se da también en gramos a
  propósito: así se contrasta con la tabla de ración impresa en el saco, sin
  tener que fiarse de la nota.
- **Coste por gato:** 18 × 1,80 = 32 € · 22 × 2,70 = 59 € → **32–59 €/año**
  (2,70–5 €/mes).
- **Recuento de contratos:** 65 de pienso + 26 de gestión = 91 («más de 90») en
  70 entidades. La fila de pienso de la tabla suma 64 + el de Aranguren, que
  está en evaluación sin fecha y no cae en ningún año.

### Estimaciones, no medidas

Conviene saber cuáles son blandas, por si alguien las discute:

- **10–12 gatos por colonia** de media (lo que se maneja en el sector).
- **~10 gatos comunitarios por cada mil habitantes** en municipios con censo.
  Es el **único dato empírico que se afirma sin fuente citada**. Pesa poco
  porque el otro método lo corrobora, pero si algún día se publica un censo
  municipal que lo respalde, conviene citarlo.
- El número de colonias de un municipio concreto: siempre un **suelo**, nunca un
  techo. Quedan colonias sin aflorar y vecinos que alimentan por su cuenta.

La nota propone cruzar los dos métodos (por colonias y por población): si
coinciden, el orden de magnitud es fiable; si divergen mucho, faltan colonias
por registrar.

## Mantenimiento

La tabla de licitaciones envejece sola. `scripts/recordatorio_licitaciones.py`
manda un correo **el 15 de enero y el 15 de julio** recordando actualizarla; lee
de `recursos.html` la fecha de los datos publicados. Ver «Tareas programadas» en
`manuales/manual-despliegue.md`.

Al actualizar la tabla hay que **reimprimir los dos PDF**, no solo uno: la nota
cita cifras que salen de la tabla (número de contratos, municipios, importes).

### Pendiente

- Reimprimir `nota-compra-publica-pienso-colonias.pdf`: el publicado es anterior
  a los cambios del 11-11-2026 (apartado 8 nuevo, precios corregidos).
- Comprobar si la columna «Cobertura teórica de necesidad de pienso» de la hoja
  de licitaciones se calculó con los 2,20–4 €/kg antiguos. Si es así, hay que
  recalcularla y reimprimir también esa tabla.
