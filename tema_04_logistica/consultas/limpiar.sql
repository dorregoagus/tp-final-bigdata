CREATE OR REPLACE TABLE rechazados_limpios AS
SELECT * REPLACE (
    CAST(fecha_despacho AS DATE) AS fecha_despacho,
    CAST(fecha_entrega AS DATE) AS fecha_entrega,
    CAST(dias_entrega AS INTEGER) AS dias_entrega
)
FROM tmp_limpios;

CREATE OR REPLACE TABLE descartados AS
SELECT * FROM tmp_descartados;