SELECT
    transportista,
    ROUND(AVG(dias_entrega), 2) AS promedio_dias_entrega
FROM tabla_final
GROUP BY transportista
ORDER BY promedio_dias_entrega ASC;

SELECT
    transportista,
    ROUND(SUM(costo_envio), 2) AS costo_total_ars
FROM tabla_final
GROUP BY transportista
ORDER BY costo_total_ars DESC;

SELECT
    origen,
    destino,
    COUNT(*) AS cantidad_envios
FROM tabla_final
GROUP BY origen, destino
ORDER BY cantidad_envios DESC
LIMIT 5;

SELECT
    destino,
    ROUND(SUM(peso_kg), 2) AS total_kg
FROM tabla_final
GROUP BY destino
ORDER BY total_kg DESC;

SELECT
    COUNT(*) AS envios_mas_de_7_dias
FROM tabla_final
WHERE dias_entrega > 7