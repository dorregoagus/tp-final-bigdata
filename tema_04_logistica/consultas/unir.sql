CREATE OR REPLACE TABLE tabla_final AS
WITH todo AS (
    SELECT
        id_envio,
        CAST(fecha_despacho AS DATE) AS fecha_despacho,
        CAST(fecha_entrega AS DATE) AS fecha_entrega,
        origen,
        destino,
        transportista,
        CAST(peso_kg AS DOUBLE) AS peso_kg,
        CAST(costo_envio AS DOUBLE) AS costo_envio,
        CAST(dias_entrega AS INTEGER) AS dias_entrega,
        1 AS prioridad
    FROM validos
    UNION ALL
    SELECT
        id_envio, fecha_despacho, fecha_entrega, origen, destino, transportista,
        peso_kg, costo_envio, dias_entrega,
        2 AS prioridad
    FROM rechazados_limpios
)
SELECT * EXCLUDE (prioridad)
FROM todo
QUALIFY row_number() OVER (PARTITION BY id_envio ORDER BY prioridad) = 1;