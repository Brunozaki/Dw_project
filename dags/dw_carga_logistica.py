"""Carrega no data warehouse a foto inicial e todos os lotes diários pendentes."""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import dag, task

from logistica.auditoria import DW_CONN_ID, registrar_execucao, registrar_falha
from logistica.carga import carregar_lote, ler_data_corte, listar_lotes, lotes_pendentes

PASTA_DADOS = os.environ.get("DW_DATA_DIR", "/opt/airflow/data")


@dag(
    dag_id="dw_carga_logistica",
    schedule="0 5 * * *",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    # Duas execuções ao mesmo tempo disputariam os mesmos lotes.
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5), "on_failure_callback": registrar_falha},
    tags=["dw", "carga"],
)
def dw_carga_logistica():
    @task
    def carregar(**context):
        dag_id, run_id = context["dag"].dag_id, context["run_id"]
        load_run_id = registrar_execucao(dag_id, run_id, "running")
        hook = PostgresHook(postgres_conn_id=DW_CONN_ID)
        ultimo = hook.get_first("SELECT max(batch_date) FROM audit.loaded_batch")[0]
        data_corte = ler_data_corte(PASTA_DADOS)
        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        pendentes = lotes_pendentes(data_corte, listar_lotes(PASTA_DADOS), ultimo, hoje)

        total = 0
        conn = hook.get_conn()
        try:
            for lote in pendentes:
                linhas = carregar_lote(conn, PASTA_DADOS, data_corte, lote, load_run_id)
                print(f"Lote {lote}: {linhas} linhas")
                total += linhas
        finally:
            conn.close()
        registrar_execucao(dag_id, run_id, "success", rows_loaded=total)

    carregar()


dw_carga_logistica()
