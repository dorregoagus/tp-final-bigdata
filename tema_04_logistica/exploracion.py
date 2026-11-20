import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import duckdb
    import pandas as pd

    return duckdb, pd


@app.cell
def _(duckdb, pd):
    df = pd.read_csv("datos/envios.csv", dtype=str)
    con = duckdb.connect()
    con.register("envios", df)
    print("filas, columnas:", df.shape)
    return con, df


@app.cell
def _(df):
    df.head(15)
    return


@app.cell
def _(df):
    df.isna().sum()
    return


@app.cell
def _(df):
    df["transportista"].value_counts(dropna=False)
    return


@app.cell
def _(df):
    df["origen"].value_counts(dropna=False)
    return


@app.cell
def _(df):
    df["destino"].value_counts(dropna=False)
    return


@app.cell
def _(con):
    con.sql("""
        SELECT id_envio, COUNT(*) AS veces
        FROM envios
        GROUP BY id_envio
        HAVING COUNT(*) > 1
        ORDER BY veces DESC
    """).df()
    return


@app.cell
def _(df):
    patron = r"^\d{4}-\d{2}-\d{2}$"
    mal_formato = (~df["fecha_despacho"].fillna("").str.match(patron)) | (~df["fecha_entrega"].fillna("").str.match(patron))
    df[mal_formato][["id_envio", "fecha_despacho", "fecha_entrega"]]
    return


@app.cell
def _(con):
    con.sql("""
        SELECT id_envio, fecha_despacho, fecha_entrega
        FROM envios
        WHERE (fecha_despacho IS NOT NULL AND TRY_CAST(fecha_despacho AS DATE) IS NULL)
           OR (fecha_entrega IS NOT NULL AND TRY_CAST(fecha_entrega AS DATE) IS NULL)
    """).df()
    return


@app.cell
def _(con):
    con.sql("""
        SELECT id_envio, fecha_despacho, fecha_entrega, dias_entrega
        FROM envios
        WHERE TRY_CAST(fecha_entrega AS DATE) < TRY_CAST(fecha_despacho AS DATE)
    """).df()
    return


@app.cell
def _(con):
    con.sql("""
        SELECT id_envio, peso_kg, costo_envio, dias_entrega
        FROM envios
        WHERE TRY_CAST(peso_kg AS DOUBLE) IS NULL OR TRY_CAST(peso_kg AS DOUBLE) <= 0
           OR TRY_CAST(costo_envio AS DOUBLE) IS NULL OR TRY_CAST(costo_envio AS DOUBLE) <= 0
           OR TRY_CAST(dias_entrega AS INTEGER) IS NULL OR TRY_CAST(dias_entrega AS INTEGER) < 0
    """).df()
    return


@app.cell
def _(con):
    con.sql("""
        SELECT id_envio, fecha_despacho, fecha_entrega, dias_entrega,
               date_diff('day', TRY_CAST(fecha_despacho AS DATE), TRY_CAST(fecha_entrega AS DATE)) AS dias_calculados
        FROM envios
        WHERE date_diff('day', TRY_CAST(fecha_despacho AS DATE), TRY_CAST(fecha_entrega AS DATE))
              <> TRY_CAST(dias_entrega AS INTEGER)
    """).df()
    return


@app.cell
def _(con):
    con.sql("""
        SELECT MIN(TRY_CAST(peso_kg AS DOUBLE)) AS peso_min, MAX(TRY_CAST(peso_kg AS DOUBLE)) AS peso_max,
               MIN(TRY_CAST(costo_envio AS DOUBLE)) AS costo_min, MAX(TRY_CAST(costo_envio AS DOUBLE)) AS costo_max,
               MIN(TRY_CAST(dias_entrega AS INTEGER)) AS dias_min, MAX(TRY_CAST(dias_entrega AS INTEGER)) AS dias_max
        FROM envios
    """).df()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
