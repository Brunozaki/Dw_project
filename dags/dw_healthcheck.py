"""Confere diariamente se o data warehouse está acessível e com as camadas criadas."""
from datetime import datetime, timedelta

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import dag, task

DW_CONN_ID = "dw_postgres"
EXPECTED_SCHEMAS = {"raw", "staging", "marts", "audit"}


@dag(
    dag_id="dw_healthcheck",
    schedule="0 6 * * *",
    start_date=datetime(2026, 11, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["dw", "infra"],
)
def dw_healthcheck():
    @task
    def check_schemas():
        hook = PostgresHook(postgres_conn_id=DW_CONN_ID)
        rows = hook.get_records("SELECT schema_name FROM information_schema.schemata")
        missing = EXPECTED_SCHEMAS - {row[0] for row in rows}
        if missing:
            raise ValueError(f"Schemas ausentes no DW: {sorted(missing)}")

    @task
    def record_run(**context):
        hook = PostgresHook(postgres_conn_id=DW_CONN_ID)
        hook.run(
            """
            INSERT INTO audit.load_run (dag_id, run_id, status)
            VALUES (%s, %s, 'success')
            ON CONFLICT (dag_id, run_id) DO NOTHING
            """,
            parameters=(context["dag"].dag_id, context["run_id"]),
        )

    check_schemas() >> record_run()


dw_healthcheck()
