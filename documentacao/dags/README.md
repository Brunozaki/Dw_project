# Pasta `dags/`

Esta pasta guarda as **DAGs**, os arquivos Python que dizem ao Airflow o que fazer e quando fazer. Uma DAG é um conjunto de tarefas com uma ordem definida.

**Por que a pasta existe:** o Airflow lê essa pasta automaticamente. Basta colocar um arquivo aqui para a DAG aparecer no site. O `docker-compose.yml` conecta a pasta ao Airflow em modo somente leitura (`:ro`), então o Airflow não consegue alterar seus arquivos.

| Arquivo | Motivo de existir |
|---|---|
| `dw_healthcheck.py` | Testa todo dia se o data warehouse está acessível e completo |
| `dw_carga_logistica.py` | Carrega os dados de logística todo dia |
| `logistica/carga.py` | Regras da carga: quais lotes faltam, como copiá-los e como validá-los |
| `logistica/auditoria.py` | Grava as execuções e as falhas em `audit.load_run` |
| `logistica/sql/` | Consultas que levam os dados de `staging` para `marts` |

## `dw_carga_logistica.py`

**Por que existe:** é a automação principal do projeto. Ela leva os arquivos de `data/` até o modelo estrela.

**Quando roda:** todo dia às 05:00, no horário de São Paulo, se estiver ativada.

**O que ela faz, em ordem:**

1. Grava a execução em `audit.load_run` com o status `running`.
2. Compara a tabela `audit.loaded_batch` com os arquivos, para descobrir quais lotes faltam. Só entram dias já encerrados.
3. Para cada lote, em ordem:
   - copia os arquivos para `raw`, substituindo uma cópia anterior do mesmo lote;
   - atualiza as dimensões em `marts`;
   - roda as validações;
   - atualiza as tabelas fato em `marts`;
   - registra o lote em `audit.loaded_batch`.
4. Grava `success` e o total de linhas.

Na primeira execução, o primeiro lote é a foto inicial, que traz o histórico e os cadastros. Ele leva vários minutos. Os lotes diários são pequenos e levam segundos.

**Dias perdidos não se perdem.** A lista de lotes vem do banco, não do horário agendado. Se o computador ficar desligado por uma semana, a próxima execução carrega os sete lotes, em ordem.

**A carga pode ser repetida.** Cada lote roda em uma transação: ou entra por inteiro, ou nada dele fica no banco. Pedidos e entregas que já existem são atualizados, não duplicados.

### Quando a carga falha

O Airflow tenta mais 2 vezes. Se continuar falhando, a execução fica com o status `failed`, e o motivo vai para a coluna `error`:

```bash
docker compose exec postgres-dw psql -U dw_admin -d dw_logistica -c "SELECT dag_id, status, error, finished_at FROM audit.load_run WHERE status = 'failed';"
```

Lotes anteriores continuam carregados. Corrija o problema e clique em **Acionar**: a carga retoma do lote que falhou.

**Validações:** impedem que um lote com problema chegue em `marts`. Elas reprovam linhas duplicadas, status desconhecido, valores negativos, entrega antes do envio e referências para cadastros ou pedidos que não existem. A mensagem de erro diz qual regra falhou e em quantas linhas. A lista fica em `VALIDACOES`, em `logistica/carga.py`.

## `dw_healthcheck.py`

**Por que existe:** prova que Airflow e banco conversam entre si e serve de modelo simples para novas DAGs. Ela **não carrega dados de logística**.

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
| `catchup=False` | Não executa todos os dias perdidos enquanto o computador esteve desligado, apenas o agendamento mais recente |
| `retries` e `retry_delay` | Se uma tarefa falhar, tenta mais 2 vezes, com 5 minutos de intervalo |
| `on_failure_callback` | Grava a falha em `audit.load_run` depois da última tentativa |
| `registrar_execucao` | Grava a execução, sem duplicar se ela for repetida |

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
7. Ative a DAG e clique em **Acionar** para testar.

Se ela não aparecer, procure o erro neste comando:

```bash
docker compose logs airflow-dag-processor
```

## Boas práticas

- **Faça cargas que possam ser repetidas.** Rodar a mesma tarefa duas vezes não pode duplicar dados.
- **Não escreva senhas no código.** Use a conexão `dw_postgres`.
- **Registre as cargas em `audit.load_run`.** Assim, dá para saber o que entrou no banco e quando.
- **Evite trabalho pesado fora das tarefas.** O Airflow lê os arquivos com frequência, então esse código rodaria o tempo todo.
