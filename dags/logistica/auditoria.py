"""Registro das execuções em audit.load_run, compartilhado pelas DAGs."""
from airflow.providers.postgres.hooks.postgres import PostgresHook

DW_CONN_ID = "dw_postgres"


def registrar_execucao(dag_id, run_id, status, rows_loaded=0, error=None):
    conn = PostgresHook(postgres_conn_id=DW_CONN_ID).get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit.load_run (dag_id, run_id, status, rows_loaded, error)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (dag_id, run_id) DO UPDATE SET
                    status = EXCLUDED.status, rows_loaded = EXCLUDED.rows_loaded,
                    error = EXCLUDED.error, finished_at = now()
                RETURNING load_run_id
                """,
                (dag_id, run_id, status, rows_loaded, error),
            )
            load_run_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return load_run_id


def registrar_falha(context):
    """Callback de tarefa: roda depois de esgotadas as novas tentativas."""
    registrar_execucao(
        context["dag"].dag_id, context["run_id"], "failed", error=str(context.get("exception"))[:2000]
    )
