# Pasta `dags/`

Esta pasta guarda as **DAGs**, os arquivos Python que dizem ao Airflow o que fazer e quando fazer. Uma DAG é um conjunto de tarefas com uma ordem definida.

**Por que a pasta existe:** o Airflow lê essa pasta automaticamente. Basta colocar um arquivo aqui para a DAG aparecer no site. O `docker-compose.yml` conecta a pasta ao Airflow em modo somente leitura (`:ro`), então o Airflow não consegue alterar seus arquivos.

| Arquivo | Motivo de existir |
|---|---|
| `dw_healthcheck.py` | Testa todo dia se o data warehouse está acessível e completo |

## `dw_healthcheck.py`

**Por que existe:** antes de carregar dados reais, é preciso provar que Airflow e banco conversam entre si. Esta DAG faz isso e serve de modelo para as próximas. Ela **não carrega dados de logística**.

**Quando roda:** todo dia às 06:00, no horário de São Paulo, se estiver ativada.

Ela tem duas tarefas, nesta ordem:

| Tarefa | O que faz |
|---|---|
| `check_schemas` | Confere se os schemas `raw`, `staging`, `marts` e `audit` existem. Se faltar algum, falha |
| `record_run` | Grava a execução com sucesso na tabela `audit.load_run` |

Como a segunda tarefa só roda se a primeira funcionar, cada linha em `audit.load_run` indica que o teste passou.

### Partes do arquivo

| Trecho | Significado |
|---|---|
| `DW_CONN_ID = "dw_postgres"` | Nome da conexão com o banco, definida em `AIRFLOW_CONN_DW_POSTGRES` no `docker-compose.yml` |
| `EXPECTED_SCHEMAS` | Lista dos schemas obrigatórios |
| `schedule="0 6 * * *"` | Horário de execução. Os campos são: minuto, hora, dia, mês e dia da semana |
| `start_date` | Data a partir da qual a DAG pode rodar |
| `catchup=False` | Não executa dias perdidos enquanto o computador esteve desligado |
| `retries` e `retry_delay` | Se uma tarefa falhar, tenta mais 2 vezes, com 5 minutos de intervalo |
| `ON CONFLICT ... DO NOTHING` | Evita linha duplicada se a mesma execução for repetida |

### Exemplos de horário

| Valor de `schedule` | Quando roda |
|---|---|
| `0 6 * * *` | Todo dia às 06:00 |
| `30 22 * * *` | Todo dia às 22:30 |
| `0 6 * * 1` | Toda segunda-feira às 06:00 |
| `None` | Só quando alguém mandar rodar |

## Como criar uma DAG nova

1. Copie o `dw_healthcheck.py` e dê um nome novo ao arquivo.
2. Troque `dag_id` por um nome único. Use letras minúsculas e `_`.
3. Troque o nome da função principal e sua chamada na última linha.
4. Escreva as tarefas e ajuste o `schedule`.
5. Salve na pasta `dags/`.
6. Espere alguns minutos até a DAG aparecer no site.
7. Ative a DAG e clique em **Trigger** para testar.

Se ela não aparecer, procure o erro neste comando:

```bash
docker compose logs airflow-dag-processor
```

## Boas práticas

- **Faça cargas que possam ser repetidas.** Rodar a mesma tarefa duas vezes não pode duplicar dados.
- **Não escreva senhas no código.** Use a conexão `dw_postgres`.
- **Registre as cargas em `audit.load_run`.** Assim, dá para saber o que entrou no banco e quando.
- **Evite trabalho pesado fora das tarefas.** O Airflow lê os arquivos com frequência, então esse código rodaria o tempo todo.
