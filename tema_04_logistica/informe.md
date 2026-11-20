# TP Final: Pipeline ETL con Python, DuckDB, pandas y Airflow

**Tema 04 – Logística: envíos (RapiCargo Logística)**
Integrantes: Falcón y Dorrego

## 1. Qué hicimos

Armamos un pipeline que lee el archivo `envios.csv` sin modificarlo y lo carga tal cual en la tabla `raw_envios` (2575 filas, no se perdió ninguna). Después lo validamos con 12 reglas: 1425 registros quedaron en `validos` y 1150 en `rechazados`. Los rechazados los limpiamos con pandas: 921 se pudieron arreglar (`rechazados_limpios`) y 229 no (quedaron en `descartados`). Al unir `validos` con `rechazados_limpios` y sacar los ids repetidos quedaron 2275 filas en `tabla_final`. Todo se ejecuta solo con Airflow todos los días a las 2:00 AM.

## 2. Problemas encontrados y rechazos por regla

Antes de armar las reglas exploramos los datos en marimo. Estos fueron los problemas y cuántos registros rechazó cada regla:

| Regla | Problema encontrado | Rechazados |
|---|---|---|
| R2 | 71 ids aparecían repetidos (75 filas de más) | 75 |
| R3 | `fecha_despacho` en otro formato (ej: 21/02/2024) | 205 |
| R4 | `fecha_entrega` en otro formato (ej: 20/01/2025) | 206 |
| R5 | `fecha_entrega` anterior al despacho (parecen cargadas al revés) | 103 |
| R6 | `peso_kg` negativo (ej: -34.12) | 103 |
| R7 | `costo_envio` con formato raro (ej: 24.624,00) | 126 |
| R8 | `transportista` en mayúsculas o con espacios (ej: MERCADO_ENVIOS_) | 207 |
| R11 | `dias_entrega` vacío | 153 |
| R12 | `dias_entrega` que no coincide con las fechas | 103 |

Las reglas R1 (id vacío), R9 (origen vacío) y R10 (destino vacío) no rechazaron nada. Un mismo registro puede romper más de una regla, por eso la suma de la tabla (1281) es mayor que los 1150 rechazados.

## 3. Limpieza de los rechazados

Con pandas sacamos los espacios sobrantes, pasamos el transportista a minúsculas, convertimos las fechas con barras al formato correcto, dejamos los negativos en positivo, cambiamos las comas decimales por puntos, completamos fechas vacías usando `dias_entrega` y recalculamos `dias_entrega` con las fechas. Lo que seguía mal después de eso quedó en `descartados`. Al unir se sacaron 71 filas repetidas (1425 + 921 = 2346, y `tabla_final` tiene 2275).

## 4. Respuestas a las preguntas de negocio

1. **Promedio de días de entrega por transportista:** andreani 4,88 – mercado_envios 5,04 – correo_argentino 5,07 – oca 5,12.
2. **Costo total de envíos por transportista (ARS):** andreani 18.773.041,94 – mercado_envios 17.985.990,94 – correo_argentino 17.546.782,82 – oca 16.436.147,61.
3. **Las 5 rutas con más envíos:** Mendoza → Buenos Aires (75), Mendoza → Bahia Blanca (69), Salta → Mendoza (69), Salta → Bahia Blanca (67) y Cordoba → Buenos Aires (63).
4. **Kg enviados por destino:** Bahia Blanca 7194,80 – Rosario 6874,66 – Buenos Aires 6798,48 – Tucuman 6739,25 – Mendoza 6633,62 – Cordoba 6286,46 – Salta 6246,32.
5. **Envíos entregados en más de 7 días:** 516.

## 5. Airflow

El DAG se llama `pipeline_logistica` y tiene 6 tareas encadenadas con `>>`: extraer, cargar_raw, validar, limpiar, unir y responder_preguntas. La programación es `0 2 * * *` (todos los días a las 2:00 AM). Lo ejecutamos a mano con Trigger y todas las tareas salieron en verde. Como usa `CREATE OR REPLACE TABLE`, se puede correr varias veces sin duplicar datos.