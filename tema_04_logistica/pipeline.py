import unicodedata
import duckdb
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
CSV = BASE / "datos" / "envios.csv"
DB = BASE / "pipeline.duckdb"
CARPETA_SQL = BASE / "consultas"

# CAMBIAR: tiene que ser la misma lista que usaste en la regla R8 de validar.sql
TRANSPORTISTAS = ["mercado_envios", "andreani", "oca", "correo_argentino"]

FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]


def conectar():
    return duckdb.connect(str(DB))


def leer_sql(nombre, **params):
    texto = (CARPETA_SQL / nombre).read_text(encoding="utf-8")
    for clave, valor in params.items():
        texto = texto.replace("{" + clave + "}", str(valor))
    return texto


def correr_sql(con, texto):
    # ejecuta varias sentencias separadas por ;
    for sentencia in texto.split(";"):
        if sentencia.strip():
            con.execute(sentencia)


# ---------- 1. EXTRAER ----------
def extraer():
    if not CSV.exists():
        raise FileNotFoundError(f"No encuentro el archivo {CSV}")
    df = pd.read_csv(CSV, dtype=str)
    print(f"Filas en el archivo original: {len(df)}")
    return len(df)


# ---------- 2. CARGAR A RAW ----------
def cargar_raw():
    con = conectar()
    correr_sql(con, leer_sql("extract.sql", ruta=CSV.as_posix()))
    filas = con.execute("SELECT COUNT(*) FROM raw_logistica").fetchone()[0]
    print(f"Filas en raw_logistica: {filas}")
    con.close()
    return filas


# ---------- 3. VALIDAR ----------
def validar():
    con = conectar()
    correr_sql(con, leer_sql("validar.sql"))
    v = con.execute("SELECT COUNT(*) FROM validos").fetchone()[0]
    r = con.execute("SELECT COUNT(*) FROM rechazados").fetchone()[0]
    print(f"Validos: {v} | Rechazados: {r}")
    con.close()


# ---------- 4. LIMPIAR ----------
def sin_tildes(texto):
    if pd.isna(texto):
        return texto
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def parsear_fecha(valor):
    if pd.isna(valor):
        return pd.NaT
    valor = str(valor).strip()
    for formato in FORMATOS_FECHA:
        try:
            return pd.to_datetime(valor, format=formato)
        except ValueError:
            continue
    return pd.NaT


def limpiar():
    con = conectar()
    df = con.execute("SELECT * FROM rechazados").df()

    # 1) espacios sobrantes en todas las columnas
    for col in df.columns:
        df[col] = df[col].str.strip()

    # 2) mayusculas, tildes y formato de texto
    df["id_envio"] = df["id_envio"].str.upper()
    for col in ["origen", "destino"]:
        df[col] = df[col].apply(sin_tildes).str.title()
    df["transportista"] = (df["transportista"].str.lower()
                           .str.replace(" ", "_").str.replace("-", "_"))

    # 3) fechas en distintos formatos
    df["fecha_despacho"] = df["fecha_despacho"].apply(parsear_fecha)
    df["fecha_entrega"] = df["fecha_entrega"].apply(parsear_fecha)

    # 4) numeros: coma decimal, negativos a positivos, cero a nulo
    for col in ["peso_kg", "costo_envio"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").abs()
        df[col] = df[col].where(df[col] > 0)
    df["dias_entrega"] = pd.to_numeric(df["dias_entrega"], errors="coerce").abs()

    # 5) nulos que se deducen de otras columnas
    dias = pd.to_timedelta(df["dias_entrega"], unit="D")

    falta_entrega = df["fecha_entrega"].isna() & df["fecha_despacho"].notna() & dias.notna()
    df.loc[falta_entrega, "fecha_entrega"] = df["fecha_despacho"] + dias

    falta_despacho = df["fecha_despacho"].isna() & df["fecha_entrega"].notna() & dias.notna()
    df.loc[falta_despacho, "fecha_despacho"] = df["fecha_entrega"] - dias

    # 6) dias_entrega siempre se recalcula con las fechas para que coincidan
    ambas = df["fecha_entrega"].notna() & df["fecha_despacho"].notna()
    df.loc[ambas, "dias_entrega"] = (df["fecha_entrega"] - df["fecha_despacho"]).dt.days

    # 7) vuelvo a chequear: lo que sigue mal no se puede arreglar
    ok = (
        df["id_envio"].notna() & (df["id_envio"] != "")
        & df["fecha_despacho"].notna() & df["fecha_entrega"].notna()
        & (df["fecha_entrega"] >= df["fecha_despacho"])
        & df["peso_kg"].notna() & df["costo_envio"].notna()
        & df["transportista"].isin(TRANSPORTISTAS)
        & df["origen"].notna() & (df["origen"] != "")
        & df["destino"].notna() & (df["destino"] != "")
        & df["dias_entrega"].notna()
    )
    limpios = df[ok].drop(columns="motivo_rechazo")
    descartados = df[~ok]

    con.register("tmp_limpios", limpios)
    con.register("tmp_descartados", descartados)
    correr_sql(con, leer_sql("limpiar.sql"))
    print(f"Limpiados: {len(limpios)} | Descartados (sin arreglo): {len(descartados)}")
    con.close()


# ---------- 5. UNIR ----------
def unir():
    con = conectar()
    correr_sql(con, leer_sql("unir.sql"))
    filas = con.execute("SELECT COUNT(*) FROM tabla_final").fetchone()[0]
    print(f"Filas en tabla_final: {filas}")
    con.close()


# ---------- 6. PREGUNTAS DE NEGOCIO ----------
def responder_preguntas():
    con = conectar()
    consultas = [q.strip() for q in leer_sql("preguntas.sql").split(";") if q.strip()]
    for i, consulta in enumerate(consultas, start=1):
        con.execute(f"CREATE OR REPLACE TABLE respuesta_{i} AS {consulta}")
        print(f"\n--- Respuesta {i} ---")
        print(con.execute(f"SELECT * FROM respuesta_{i}").df())
    con.close()


def correr_todo():
    extraer()
    cargar_raw()
    validar()
    limpiar()
    unir()
    responder_preguntas()


if __name__ == "__main__":
    correr_todo()