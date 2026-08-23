# Migraciones de base de datos

Una migración lleva una base de datos **que ya tiene datos** de una versión a la
siguiente. Aquí está cuándo hacen falta, cómo saberlo, y cómo ensayarlas antes
de tocar el servidor.

Los ficheros `.sql` viven en `scripts/migraciones/`.

## Por qué existen

`docker/init/modelo-fisico.sql` está montado en `/docker-entrypoint-initdb.d/`,
y MariaDB solo ejecuta lo que hay ahí **cuando el directorio de datos está
vacío**. En un despliegue con datos no se vuelve a ejecutar nunca.

Eso tiene dos consecuencias que no son obvias:

- **Una columna nueva no aparece sola.** Pero el modelo ORM sí la mapea, así que
  la API pediría `SELECT … columna_nueva …` contra una tabla que no la tiene:
  error 1054 y **500 en la portada**.
- **`cargar_dataset` no arregla datos ya cargados.** Es aditivo: inserta lo que
  falta, pero no reescribe filas existentes. No corrige nombres ni fusiona
  entidades duplicadas.

> **Nunca `reset-db` en el servidor.** Borraría la cuenta de administración y las
> `fecha_fin_plazo`, que no están en el dataset y se rellenan a mano desde el
> panel.

## Cómo saber si el despliegue que viene necesita una

Antes de desplegar, comparar lo que va a `main` con lo que corre en el servidor
(la última etiqueta desplegada):

```bash
# ¿Cambió el esquema?
git diff v1.6..main -- docker/init/modelo-fisico.sql

# ¿Cambió el modelo ORM?
git diff v1.6..main -- backend/app/models.py

# ¿Cambió el dataset o el pipeline que lo genera?
git diff --stat v1.6..main -- data/final/ scripts/data_processing/
```

**Si el primero o el segundo tienen salida, hace falta migración.** No hay
excepción: cualquier columna añadida, renombrada o borrada rompe la API si no se
aplica también en el servidor.

Si solo cambió el tercero, depende: datos **nuevos** los carga `cargar_dataset`
sin más, pero **correcciones sobre filas existentes** necesitan migración.

## Cómo escribirlas

- Un fichero por migración, `AAAA-MM-DD_descripcion.sql`, en `scripts/migraciones/`.
- **Idempotentes**: lanzarlas dos veces no puede estropear nada. `ADD COLUMN IF
  NOT EXISTS`, `UPDATE` con valores absolutos, y comprobar antes de borrar o
  fusionar.
- Comentar **de dónde sale cada dato**. Una migración que corrige datos públicos
  tiene que poder justificarse: en `2026-08-23_periodo_y_erratas.sql` cada
  corrección lleva su fuente (BOE, BDNS, registro de asociaciones).
- Cuidado con los nombres de columna: se escriben de memoria y **no coinciden con
  los del ORM**. `Agrupacion.id_represent` es `id_represent` en la tabla, no
  `id_benef_representante`. Ese error concreto tumbó el primer ensayo.

## Cómo ensayarlas

Esto no es opcional para una migración que toca datos. Se monta una réplica del
estado del servidor en una base aparte y se lanza ahí primero.

```bash
# 1. Sacar el esquema y el dataset de la versión que corre en el servidor
git show v1.6:docker/init/modelo-fisico.sql > /tmp/esquema_v16.sql
git show v1.6:data/final/dataset_unificado.json > /tmp/dataset_v16.json
git show v1.6:data/final/causas_exclusion.json > /tmp/causas_v16.json
git show v1.6:scripts/data_processing/cargar_dataset.py > /tmp/cargar_v16.py

# 2. Redirigir el esquema a la base de ensayo: el fichero trae su propio
#    `USE bdns_dgda` y si no se cambia escribe en la base real
sed -E 's/bdns_dgda/bdns_ensayo/g' /tmp/esquema_v16.sql > /tmp/esquema_ensayo.sql

# 3. Crearla y cargarla (ver el detalle en el historial de implementación)
#    Importante: añadir a mano lo que el dataset NO trae y el servidor sí tiene
#    —las convocatorias que insertó el cron y la cuenta de administración—,
#    porque son justo las que una migración mal escrita se lleva por delante.

# 4. Lanzar la migración contra bdns_ensayo, y comprobar TRES cosas:
#      · que no da error
#      · que el resultado es idéntico al de una carga limpia desde el pipeline
#      · que lanzarla una segunda vez no cambia nada
#      · que la cuenta de administración sigue ahí

# 5. Borrar la réplica
DROP DATABASE bdns_ensayo;
```

La comparación del punto 4 es la que de verdad prueba algo: si la base migrada
queda igual que una cargada desde cero, la migración es correcta.

## Cómo aplicarlas en el servidor

En `manuales/manual-despliegue.md`, apartado «Cuando el despliegue trae cambios
de esquema o de datos». Resumen: backup, migración, y **después** reconstruir el
backend — al revés, el servidor sirve 500 hasta que la migración pase.

## Historial

| Fichero | Qué hace |
|---|---|
| `2026-08-23_periodo_y_erratas.sql` | Añade `periodo_anio` y `periodo_matiz`; corrige el periodo de las 10 convocatorias, incluida la EELL de 2023 que constaba como anual siendo semestral; corrige el nombre de Carlet y Carrión de Calatrava; y fusiona las cinco entidades que el BOE publicó con dos CIF distintos |
