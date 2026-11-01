# Dw_project
Projeto de Data Warehouse voltado a dados de logistica, utilizando sistema Linux, PostgresSQL, Airflow e Docker. Pensando em ser um carregador de dados automatizado para atualizar os dados do warehouse diariamente, com confiabilidade e persistência de dados.

## Arquitetura

| Serviço | Função | Acesso |
|---|---|---|
| `postgres-dw` | Data warehouse (Postgres 17) | `localhost:5433` |
| `postgres-airflow` | Metadados do Airflow | interno |
| `airflow-apiserver` | Interface web e API | http://localhost:8080 |
| `airflow-scheduler` | Agenda e executa as tarefas (`LocalExecutor`) | interno |
| `airflow-dag-processor` | Lê as DAGs | interno |

Os dados ficam em volumes do Docker e sobrevivem à recriação dos containers.

| Camada | Conteúdo |
|---|---|
| `raw` | Dados como vieram da origem |
| `staging` | Dados limpos e padronizados |
| `marts` | Modelo estrela para análise |
| `audit` | Registro das cargas |

## Estrutura

```text
dags/          DAGs do Airflow
documentacao/  Guias detalhados, organizados como as pastas do projeto
scripts/       Configuração do ambiente
sql/dw/        Criação do DW, executada na primeira subida do volume
```

Para instalar o projeto do zero, siga o guia [Como aplicar](documentacao/como-aplicar.md).

## Como rodar

Requer Docker Engine com Compose no Ubuntu do WSL2. Os comandos abaixo rodam no Ubuntu, na raiz do projeto (`/mnt/d/Repositorio/Dw_project`).

Instale o Docker, se necessário, e reabra o terminal:

```bash
sudo bash scripts/setup-docker-wsl.sh "$USER"
```

Crie o `.env` e suba os serviços:

```bash
bash scripts/create-env.sh
docker compose up -d
```

Acesse http://localhost:8080 com o usuário `admin` e a senha de `AIRFLOW_ADMIN_PASSWORD`, no `.env`. As DAGs começam pausadas: ative a `dw_healthcheck` e dispare uma execução para testar.

Os arquivos de `sql/dw` só rodam quando o volume do DW é criado. Para reaplicá-los do zero, o que **apaga os dados do DW**:

```bash
docker compose down -v
```
