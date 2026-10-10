# EELL — los documentos de cada convocatoria

El Ministerio publica **muchos más documentos de los que parece**, con nombres
parecidos que significan cosas distintas, y **la estructura cambia cada año**.
No hay un esquema fijo al que agarrarse: lo que sigue es lo que se repite, no
una plantilla.

## Lo que siempre ocurre, en orden

| Fase | Qué hace | ¿Puntuaciones e importes? | ¿BOE? |
|---|---|---|---|
| Convocatoria | Abre el plazo | — | Extracto |
| **Relación provisional** de admitidas y excluidas | Quién entra al proceso, con la causa. Abre plazo para **subsanar** | No | No |
| **Relación definitiva** de admitidas y excluidas | Cierra quién concurre | No | No |
| **Propuesta / resolución provisional de concesión** | Valoración hecha: puntuación, corte por tramo e importes. Solo cabe **alegar**, no aportar documentos nuevos | Sí | No |
| **Propuesta de resolución definitiva** | Tras resolver alegaciones | Sí | No |
| **Resolución de concesión** | La única con efectos | Sí | **Sí** |

## Y lo que cambia de un año a otro

- **Cuántos documentos hay.** En 2023 la relación definitiva y la propuesta
  provisional van **en el mismo PDF**; en 2024 van separadas; en 2025 la página
  llega a listar doce enlaces.
- **Cómo se llaman.** «Propuesta provisional de concesión» en un año,
  «Resolución provisional de concesión» en otro. «Relación provisional de
  solicitudes admitidas y excluidas» pasa a «…admitidas y excluidas **a
  trámite**».
- **Las correcciones de errores.** Aparecen intercaladas y **cambian el
  contenido ya publicado**: en 2025 hay dos correcciones de la convocatoria y
  otras dos de la relación definitiva. Quien se descargó la primera versión
  tiene un documento que ya no vale.
- **Resoluciones de trámite sueltas** que no afectan a los datos pero ocupan
  sitio en la lista: designación de vocales de la comisión de evaluación,
  cambios en su composición.

**Consecuencia práctica:** al guardar un documento conviene anotar en el README
del año qué fase es exactamente, porque el nombre del fichero no basta para
saberlo y el año siguiente se llamará de otra forma.

## Qué hay guardado

| Año | Relación provisional | Provisional de concesión | Propuesta definitiva | Resolución (BOE) |
|---|---|---|---|---|
| 2023 | ✔ | — | — | ✔ |
| 2024 | — | ✔ *(anexos como imagen)* | — | ✔ |
| 2025 | — | ✔ | — | ✔ |
| 2026 | — | ✔ | — | *pendiente* |

De cada año se conservan **dos documentos de los seis u ocho** que llega a
publicar el Ministerio. No es un descuido: los demás desaparecen del portal al
avanzar el trámite y nadie los guardó a tiempo. A partir de ahora conviene
bajarlos según salen.

## Lo que se ha podido medir con esto

**Entre la fase 1 y la 4, las exclusiones casi desaparecen.** En 2023 había
**490 excluidas** en la lista provisional y quedaron **39** en la definitiva:
451 entidades subsanaron a tiempo, el 92 %. Detalle en `2023/README.md`.

**Entre la fase 2 y la 4, en cambio, apenas se mueve nada.** En 2025 las
concedidas pasaron de 39 a 40 y las 303 excluidas se quedaron en 303. Detalle
en `2025/README.md`.

No es contradictorio: en la fase 1 se subsana documentación y por eso se salva
casi todo el mundo; en la fase 2 la valoración ya está hecha y solo caben
alegaciones, que mueven poco.

## Un desajuste entre años que conviene mirar antes de comparar

Los estados de la resolución definitiva no se reparten igual en todos los años:

| Año | Desistidas | Excluidas | Concedidas |
|---|---|---|---|
| 2023 | 197 | 39 | 60 |
| 2024 | 148 | 84 | 55 |
| 2025 | **1** | **303** | 40 |

El salto de 2025 es demasiado brusco para ser un cambio de comportamiento de
las entidades. Puede ser que la convocatoria clasificara distinto, o que
influya el origen del dato —2025 se cargó del XML del BOE y los dos anteriores
de PDF—. **No está investigado.** Hasta que lo esté, conviene no comparar
«desistidas» ni «excluidas» entre 2025 y los años anteriores: el total y las
concedidas sí son comparables.

## Lo que se ve al mirar los tres años juntos

Esto **no sale de estos PDF** sino del dataset ya cargado (2023–2025, 3.045
solicitudes); se anota aquí porque es donde se busca lo de EELL. El denominador
de municipios, 8.132, es el mismo que usa el estudio de Consejos para Mascotas
que ya cita la web.

**Casi nadie pide esta ayuda.** Ayuntamientos distintos que se han presentado
**alguna vez** en tres convocatorias: **1.737 de 8.132, el 21 %**. Cuatro de
cada cinco municipios no lo han pedido ni una sola vez.

Y han cobrado alguna vez **150 entidades**, de las que **144 son ayuntamientos**
—las otras seis son tres diputaciones, dos mancomunidades y una entidad local
menor—: el **1,8 %** de los municipios. El matiz importa al publicarlo, porque
las 150 no son 150 municipios.

**Y de quien lo pide, cada año entra menos.**

| Año | Solicitudes | Concedidas | % |
|---|---:|---:|---:|
| 2023 | 593 | 60 | 10,1 % |
| 2024 | 1.137 | 55 | 4,8 % |
| 2025 | 1.315 | 40 | 3,0 % |

Suben los solicitantes y baja el reparto. Este es el corte que **sí** es
comparable entre años: afecta a `concedida`, no a los estados que descuadran en
el apartado anterior.

**Insistir no da ventaja, y es el dato más duro.** 335 entidades se presentaron
los tres años: **278 (83 %) no han cobrado nunca**. De las 640 que se
presentaron dos años, el **90,5 %** tampoco. Ninguna entidad ha cobrado los tres
años; solo 5 han cobrado dos veces (las que están en la frase de recurrencia de
la web).

**Las agrupaciones son marginales, no la explicación.** Aparecen por primera vez
en 2025: **13 solicitudes**, 72 municipios implicados en total. No explican los
6.400 municipios ausentes.

**Lo que esto NO dice.** Cuántos municipios *podrían* haber pedido la ayuda. El
dataset sabe quién solicitó, no quién tiene colonias, ni quién conocía la línea.
Esa parte se intuye, no se mide.

**Nada de esto está publicado en la web todavía.** Son candidatos claros: el
21 %, el 1,8 % y el 83 % cuentan la historia de esta línea mejor que cualquier
KPI que haya ahora.

## Lo que falta

**La fase 3 de cualquier año.** Nunca se ha guardado. Serviría para repartir
ese «apenas se mueve nada» entre lo que cambian las alegaciones y lo que
cambian las renuncias de última hora.
