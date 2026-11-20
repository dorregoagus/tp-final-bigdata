import sys
from pathlib import Path
import pendulum

try:
    from airflow.sdk import DAG
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO))

import pipeline

zona = pendulum.timezone("America/Argentina/Buenos_Aires")

with DAG(
    dag_id="pipeline_logistica",
    description="Pipeline ETL de envios: raw -> validos/rechazados -> limpios -> final",
    start_date=pendulum.datetime(2026, 11, 1, tz=zona),
    schedule="0 2 * * *",      # todos los dias a las 2:00 AM
    catchup=False,
    tags=["tp_final", "logistica"],
) as dag:

    t_extraer = PythonOperator(task_id="extraer", python_callable=pipeline.extraer)
    t_cargar = PythonOperator(task_id="cargar_raw", python_callable=pipeline.cargar_raw)
    t_validar = PythonOperator(task_id="validar", python_callable=pipeline.validar)
    t_limpiar = PythonOperator(task_id="limpiar", python_callable=pipeline.limpiar)
    t_unir = PythonOperator(task_id="unir", python_callable=pipeline.unir)
    t_preguntas = PythonOperator(task_id="responder_preguntas", python_callable=pipeline.responder_preguntas)

    t_extraer >> t_cargar >> t_validar >> t_limpiar >> t_unir >> t_preguntas