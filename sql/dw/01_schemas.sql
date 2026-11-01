-- Camadas do data warehouse.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS audit;

COMMENT ON SCHEMA raw IS 'Dados como vieram da origem';
COMMENT ON SCHEMA staging IS 'Dados limpos e padronizados';
COMMENT ON SCHEMA marts IS 'Modelo dimensional para análise';
COMMENT ON SCHEMA audit IS 'Rastreabilidade das cargas';

CREATE TABLE IF NOT EXISTS audit.load_run (
    load_run_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dag_id       text        NOT NULL,
    run_id       text        NOT NULL,
    status       text        NOT NULL,
    rows_loaded  bigint      NOT NULL DEFAULT 0,
    finished_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dag_id, run_id)
);
