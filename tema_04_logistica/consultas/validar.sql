CREATE OR REPLACE TABLE validacion AS
SELECT
    *,
    concat_ws(' | ',
        CASE WHEN id_envio IS NULL OR trim(id_envio) = ''
             THEN 'R1 id_envio vacio' END,
        CASE WHEN id_envio IS NOT NULL AND nro_repeticion > 1
             THEN 'R2 id_envio duplicado' END,
        CASE WHEN TRY_CAST(fecha_despacho AS DATE) IS NULL
             THEN 'R3 fecha_despacho invalida o nula' END,
        CASE WHEN TRY_CAST(fecha_entrega AS DATE) IS NULL
             THEN 'R4 fecha_entrega invalida o nula' END,
        CASE WHEN TRY_CAST(fecha_entrega AS DATE) < TRY_CAST(fecha_despacho AS DATE)
             THEN 'R5 fecha_entrega anterior a fecha_despacho' END,
        CASE WHEN TRY_CAST(peso_kg AS DOUBLE) IS NULL OR TRY_CAST(peso_kg AS DOUBLE) <= 0
             THEN 'R6 peso_kg no es numero mayor a 0' END,
        CASE WHEN TRY_CAST(costo_envio AS DOUBLE) IS NULL OR TRY_CAST(costo_envio AS DOUBLE) <= 0
             THEN 'R7 costo_envio no es numero mayor a 0' END,
        CASE WHEN transportista IS NULL
                  OR transportista NOT IN ('mercado_envios', 'andreani', 'oca', 'correo_argentino')
             THEN 'R8 transportista no permitido' END,
        CASE WHEN origen IS NULL OR trim(origen) = '' OR origen <> trim(origen)
             THEN 'R9 origen vacio o con espacios' END,
        CASE WHEN destino IS NULL OR trim(destino) = '' OR destino <> trim(destino)
             THEN 'R10 destino vacio o con espacios' END,
        CASE WHEN TRY_CAST(dias_entrega AS INTEGER) IS NULL OR TRY_CAST(dias_entrega AS INTEGER) < 0
             THEN 'R11 dias_entrega no es entero mayor o igual a 0' END,
        CASE WHEN date_diff('day', TRY_CAST(fecha_despacho AS DATE), TRY_CAST(fecha_entrega AS DATE))
                  <> TRY_CAST(dias_entrega AS INTEGER)
             THEN 'R12 dias_entrega no coincide con las fechas' END
    ) AS motivos
FROM (
    SELECT
        *,
        row_number() OVER (PARTITION BY id_envio ORDER BY rowid) AS nro_repeticion
    FROM raw_logistica
);

CREATE OR REPLACE TABLE validos AS
SELECT * EXCLUDE (nro_repeticion, motivos)
FROM validacion
WHERE motivos = '';

CREATE OR REPLACE TABLE rechazados AS
SELECT * EXCLUDE (nro_repeticion, motivos), motivos AS motivo_rechazo
FROM validacion
WHERE motivos <> '';