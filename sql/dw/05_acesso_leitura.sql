-- Papel somente leitura para relatórios. Ele não entra no banco sozinho: veja
-- documentacao/sql/dw/README.md para criar um usuário com senha própria.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dw_leitura') THEN
        CREATE ROLE dw_leitura NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA marts, audit TO dw_leitura;
GRANT SELECT ON ALL TABLES IN SCHEMA marts, audit TO dw_leitura;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts, audit GRANT SELECT ON TABLES TO dw_leitura;
