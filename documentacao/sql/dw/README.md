# Pasta `sql/dw/`

Esta pasta guarda os arquivos que criam a estrutura do data warehouse: schemas, tabelas e dados de calendário.

**Por que a pasta existe:** com a estrutura escrita em arquivos, o banco pode ser recriado do mesmo jeito em qualquer computador, e toda mudança fica registrada no Git.

**Como os arquivos são executados:** o `docker-compose.yml` conecta esta pasta ao Postgres em `/docker-entrypoint-initdb.d`. Na primeira vez que o volume do banco é criado, o Postgres roda os arquivos em ordem alfabética. Por isso, os nomes começam com números.

**Eles só rodam nessa primeira vez.** Alterar um arquivo depois não muda um banco já criado. Veja [Como alterar as tabelas](#como-alterar-as-tabelas).

| Arquivo | Motivo de existir |
|---|---|
| `01_schemas.sql` | Cria as camadas do data warehouse e o registro de cargas |
| `02_marts_logistica.sql` | Cria o modelo estrela inicial de logística |

## `01_schemas.sql`

**Por que existe:** separar os dados em camadas permite conferir cada etapa. Se um número estiver errado, dá para ver onde ele mudou. Os dados originais também ficam guardados, para reprocessar quando necessário.

Os dados andam pelas camadas nesta ordem:

```text
Origem → raw → staging → marts → relatórios
```

| Schema | Conteúdo | Exemplo |
|---|---|---|
| `raw` | Dados exatamente como vieram da origem | Arquivo importado, sem alterações |
| `staging` | Dados limpos e padronizados | Datas corrigidas e duplicados removidos |
| `marts` | Dados organizados para análise | Tabelas usadas nos relatórios |
| `audit` | Registro do funcionamento das cargas | Cada carga que rodou |

### Tabela `audit.load_run`

**Por que existe:** registra cada execução, para responder quando uma carga rodou e quantas linhas trouxe.

| Coluna | Significado |
|---|---|
| `load_run_id` | Número único da execução, gerado automaticamente |
| `dag_id` | Nome da DAG |
| `run_id` | Identificador da execução no Airflow |
| `status` | Resultado da execução |
| `rows_loaded` | Quantidade de linhas carregadas |
| `finished_at` | Data e hora do registro |

A combinação de `dag_id` e `run_id` não se repete, então uma execução não é registrada duas vezes.

## `02_marts_logistica.sql`

**Por que existe:** define o modelo estrela, que deixa as perguntas de negócio simples de responder, como "qual transportadora mais atrasa?".

> **Atenção:** este é um modelo inicial, pois a fonte de dados real ainda não foi definida. Colunas e tabelas devem ser revistas quando ela for escolhida.

```text
 dim_carrier     dim_date
          \       /
        fact_shipment
              |
         dim_location
```

| Tabela | Tipo | Conteúdo |
|---|---|---|
| `marts.fact_shipment` | Fato | Uma linha por entrega |
| `marts.dim_date` | Dimensão | Uma linha por dia, de 2020 a 2035 |
| `marts.dim_carrier` | Dimensão | Transportadoras |
| `marts.dim_location` | Dimensão | Origens e destinos |

### `marts.fact_shipment`

| Coluna | Significado |
|---|---|
| `shipment_key` | Número interno da entrega |
| `shipment_code` | Código da entrega no sistema de origem. Não se repete |
| `carrier_key` | Transportadora |
| `origin_location_key` | Local de origem |
| `destination_location_key` | Local de destino |
| `shipped_date_key` | Data de envio |
| `promised_date_key` | Data prometida. Pode ficar vazia |
| `delivered_date_key` | Data de entrega. Fica vazia até a entrega acontecer |
| `weight_kg` | Peso em quilos |
| `freight_cost` | Custo do frete |
| `load_run_id` | Carga que trouxe a linha, ligada a `audit.load_run` |

### Por que existe uma tabela de datas

A `marts.dim_date` já traz ano, trimestre, mês, dia da semana e fim de semana. Assim, um relatório por trimestre não precisa calcular nada. A chave usa o formato `AAAAMMDD`: o dia 01/11/2026 é `20261101`.

Quando chegar perto de 2035, será preciso adicionar mais anos.

### Exemplo de consulta

Entregas e custo de frete por transportadora:

```sql
SELECT c.carrier_name,
       count(*)            AS entregas,
       sum(f.freight_cost) AS custo_total
FROM marts.fact_shipment AS f
JOIN marts.dim_carrier AS c USING (carrier_key)
GROUP BY c.carrier_name
ORDER BY custo_total DESC;
```

O resultado fica vazio até existir uma carga de dados.

## Como alterar as tabelas

Os arquivos usam `IF NOT EXISTS`, então podem ser reaplicados com segurança. Isso cria o que falta, mas **não altera uma tabela que já existe**. Para adicionar uma tabela nova ao banco atual:

1. Inclua a tabela no arquivo `.sql`, para ela existir em instalações futuras.
2. Na pasta do projeto, aplique o arquivo ao banco atual:

```bash
docker compose exec -T postgres-dw psql -U dw_admin -d dw_logistica < sql/dw/02_marts_logistica.sql
```

3. Confira as tabelas:

```bash
docker compose exec postgres-dw psql -U dw_admin -d dw_logistica -c "\dt marts.*"
```

Para mudar uma tabela que já existe, como adicionar uma coluna, altere o arquivo `.sql` e rode também um comando `ALTER TABLE` no banco atual.

Em um ambiente sem dados importantes, a alternativa é recriar tudo. **Isso apaga todos os dados do data warehouse:**

```bash
docker compose down -v
```

```bash
docker compose up -d
```

Para mudanças maiores, crie um arquivo novo, como `03_nome_da_mudanca.sql`. Assim, a ordem fica clara.
