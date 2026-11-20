import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell
def _():
    import duckdb

    con = duckdb.connect("pipeline.duckdb")
    resultado = con.sql("""
        SELECT regla, COUNT(*) AS cantidad
        FROM (SELECT unnest(string_split(motivo_rechazo, ' | ')) AS regla FROM rechazados)
        GROUP BY regla ORDER BY regla;
    """).df()

    resultado
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
