CREATE OR REPLACE TABLE raw_logistica AS
SELECT *
FROM read_csv('{ruta}', header = true, all_varchar = true);