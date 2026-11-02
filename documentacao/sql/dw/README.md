# Pasta `sql/dw/`

Esta pasta guarda os arquivos que criam a estrutura do data warehouse: schemas, tabelas e dados de calendário.

**Por que a pasta existe:** com a estrutura escrita em arquivos, o banco pode ser recriado do mesmo jeito em qualquer computador, e toda mudança fica registrada no Git.

**Como os arquivos são executados:** o `docker-compose.yml` conecta esta pasta ao Postgres em `/docker-entrypoint-initdb.d`. Na primeira vez que o volume do banco é criado, o Postgres roda os arquivos em ordem alfabética. Por isso, os nomes começam com números.

**Eles só rodam nessa primeira vez.** Alterar um arquivo depois não muda um banco já criado. Veja [Como alterar as tabelas](#como-alterar-as-tabelas).

| Arquivo | Motivo de existir |
|---|---|
| `01_schemas.sql` | Cria as camadas do data warehouse e o registro de cargas |
| `02_marts_logistica.sql` | Cria o modelo estrela de logística |
| `03_raw.sql` | Cria as tabelas de chegada dos arquivos |
| `04_staging.sql` | Cria as visões que limpam os dados |
| `05_acesso_leitura.sql` | Cria o papel `dw_leitura`, para relatórios |

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
| `status` | `running`, `success` ou `failed` |
| `rows_loaded` | Quantidade de linhas carregadas |
| `error` | Motivo da falha, quando houver |
| `finished_at` | Data e hora do último registro |

A combinação de `dag_id` e `run_id` não se repete, então uma execução não é registrada duas vezes.

### Tabela `audit.loaded_batch`

**Por que existe:** guarda quais lotes já entraram no banco. A carga usa essa lista para saber o que falta, inclusive depois de dias parada.

## `02_marts_logistica.sql`

**Por que existe:** define o modelo estrela, que deixa as perguntas de negócio simples de responder, como "qual transportadora mais atrasa?". As colunas seguem os arquivos de `scripts/gerar_dados_logistica.py`.

```text
 dim_customer   dim_distribution_center   dim_product
          \            |                 /
           fact_order ---- fact_order_item
              |      \
              |       fact_invoice
              |      /
           fact_shipment ---- dim_carrier, dim_location
```

| Tabela | Tipo | Conteúdo |
|---|---|---|
| `marts.fact_order` | Fato | Uma linha por pedido, com status e valores |
| `marts.fact_order_item` | Fato | Uma linha por item de pedido |
| `marts.fact_invoice` | Fato | Uma linha por nota fiscal |
| `marts.fact_shipment` | Fato | Uma linha por entrega |
| `marts.dim_date` | Dimensão | Uma linha por dia, de 2020 a 2035 |
| `marts.dim_customer` | Dimensão | Clientes |
| `marts.dim_product` | Dimensão | Produtos |
| `marts.dim_distribution_center` | Dimensão | Centros de distribuição |
| `marts.dim_carrier` | Dimensão | Transportadoras e seu modal |
| `marts.dim_location` | Dimensão | Cidades, com região e coordenadas |

### `marts.fact_shipment`

| Coluna | Significado |
|---|---|
| `shipment_key` | Número interno da entrega |
| `shipment_code` | Código da entrega no sistema de origem. Não se repete |
| `order_key` | Pedido entregue |
| `invoice_key` | Nota fiscal da entrega |
| `carrier_key` | Transportadora |
| `origin_location_key` | Local de origem |
| `destination_location_key` | Local de destino |
| `shipped_date_key` | Data de envio |
| `promised_date_key` | Data prometida. Pode ficar vazia |
| `delivered_date_key` | Data de entrega. Fica vazia até a entrega acontecer |
| `transport_mode` | Modal usado |
| `distance_km` | Distância aproximada |
| `weight_kg` | Peso em quilos |
| `volume_m3` | Volume em metros cúbicos |
| `freight_cost` | Custo do frete |
| `occurrence` | Ocorrência da entrega, como atraso ou avaria |
| `is_late` | Se atrasou. Calculada pelo banco, fica vazia até a entrega acontecer |
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

## `03_raw.sql`

**Por que existe:** guarda os arquivos como vieram, com todas as colunas em texto. Assim, um valor estranho chega ao banco e pode ser investigado, em vez de impedir a leitura do arquivo.

Cada tabela tem a coluna `lote`, com a data do lote, e `carregado_em`. O mesmo pedido pode aparecer em vários lotes, um para cada mudança de status. Isso guarda o histórico de cada pedido.

## `04_staging.sql`

**Por que existe:** limpa os dados e converte cada coluna para o tipo certo. São visões, não tabelas: não ocupam espaço e sempre refletem o `raw`.

As visões têm o mesmo nome das tabelas do `raw`, como `staging.pedidos`.

## `05_acesso_leitura.sql`

**Por que existe:** relatórios não precisam de permissão para alterar dados. O papel `dw_leitura` só consegue ler `marts` e `audit`.

### Usuário somente leitura

O papel não tem senha e não entra no banco sozinho. Para criar um usuário, abra o banco e rode o comando abaixo, trocando o nome e a senha:

```sql
CREATE ROLE nome_do_usuario LOGIN PASSWORD 'troque-esta-senha' IN ROLE dw_leitura;
```

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
