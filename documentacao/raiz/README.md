# Raiz do projeto

A raiz é a pasta principal do projeto. Ela guarda os arquivos que configuram o projeto como um todo.

| Arquivo | Motivo de existir | Quando mexer |
|---|---|---|
| `docker-compose.yml` | Define quais serviços rodam e como se conectam | Ao adicionar ou ajustar serviços |
| `.env.example` | Modelo das configurações, sem senhas reais | Ao criar uma nova configuração |
| `.env` | Guarda as senhas reais. Não vai para o GitHub | Ao trocar uma porta |
| `.gitignore` | Lista o que o Git deve ignorar | Ao surgir um arquivo que não deve ser versionado |
| `.gitattributes` | Mantém os arquivos no formato usado pelo Linux | Raramente |
| `README.md` | Apresenta o projeto na página do GitHub | Ao mudar a visão geral do projeto |

## `docker-compose.yml`

**Por que existe:** sem ele, seria preciso iniciar cada programa manualmente, com vários comandos longos. Com ele, `docker compose up -d` sobe tudo de uma vez, sempre do mesmo jeito.

O arquivo define seis serviços:

| Serviço | Função |
|---|---|
| `postgres-dw` | Banco do data warehouse, onde ficam os dados de logística |
| `postgres-airflow` | Banco interno do Airflow, com histórico e configurações |
| `airflow-init` | Prepara o banco do Airflow e cria o usuário administrador. Roda uma vez e termina |
| `airflow-apiserver` | Site do Airflow, acessado em `localhost:8080` |
| `airflow-scheduler` | Decide quando cada tarefa roda e a executa |
| `airflow-dag-processor` | Lê os arquivos da pasta `dags/` |

### Decisões do arquivo

- **Dois bancos separados:** assim, os dados do negócio não se misturam com os dados internos do Airflow. Um pode ser recriado sem afetar o outro.
- **`LocalExecutor`:** as tarefas rodam dentro do próprio scheduler. Para uma só máquina, isso dispensa serviços extras, como Redis e Celery.
- **Sem o serviço `triggerer`:** ele só é necessário para tarefas que esperam eventos externos sem ocupar recursos, e nenhuma DAG usa isso. Por isso, o item **Disparador** aparece em vermelho na tela do Airflow, o que é esperado.
- **Versões fixas:** `apache/airflow:3.3.2` e `postgres:17.11` garantem que todos usem as mesmas versões. Versões novas só entram quando alguém altera o arquivo e testa.
- **Volumes:** os dados dos bancos e os logs ficam em `postgres-dw-data`, `postgres-airflow-data` e `airflow-logs`. Eles sobrevivem à recriação dos containers.
- **Acesso só pelo próprio computador:** as portas usam `127.0.0.1`, então outras máquinas da rede não acessam os serviços.
- **`restart: unless-stopped`:** se um serviço falhar, o Docker o reinicia. Isso não acontece se você mesmo o tiver parado.
- **Senhas obrigatórias:** a marcação `${VARIAVEL:?}` impede a subida se faltar uma configuração. Assim, nenhum serviço roda com senha vazia ou padrão.

## `.env.example` e `.env`

**Por que existem:** senhas não podem ir para o GitHub, mas as pessoas precisam saber quais configurações existem. Por isso são dois arquivos:

- `.env.example` vai para o GitHub e mostra os nomes das configurações. A palavra `gerar` marca onde entra uma senha.
- `.env` fica só no seu computador e guarda as senhas reais. Ele é criado por `scripts/create-env.sh`.

| Configuração | Significado |
|---|---|
| `AIRFLOW_DB_USER`, `AIRFLOW_DB_NAME`, `AIRFLOW_DB_PASSWORD` | Acesso ao banco interno do Airflow |
| `DW_USER`, `DW_DB`, `DW_PASSWORD` | Acesso ao data warehouse |
| `DW_PORT` | Porta do data warehouse no computador. O padrão é `5433`, para não conflitar com um Postgres já instalado |
| `AIRFLOW_PORT` | Porta do site do Airflow |
| `AIRFLOW_ADMIN_USER`, `AIRFLOW_ADMIN_PASSWORD` | Login do site do Airflow |
| `AIRFLOW_JWT_SECRET` | Segredo usado na comunicação interna do Airflow |
| `FERNET_KEY` | Chave que criptografa as senhas guardadas pelo Airflow |

**Cuidado ao trocar as senhas dos bancos:** elas são gravadas quando o volume é criado. Depois disso, mudar o `.env` não muda a senha dentro do banco, e os serviços param de conectar.

## `.gitignore`

**Por que existe:** impede que arquivos indesejados vão para o GitHub. O mais importante é o `.env`. Ele também ignora arquivos temporários do Python, ambientes virtuais e configurações de editores.

## `.gitattributes`

**Por que existe:** Windows e Linux marcam o fim de uma linha de formas diferentes (CRLF e LF). Um script salvo no formato do Windows pode falhar no Linux. Esse arquivo garante o formato LF, usado pelo Linux, nos arquivos do repositório.

## `README.md`

**Por que existe:** é a primeira página que aparece no GitHub. Ele resume o projeto, enquanto os detalhes ficam nesta pasta `documentacao`.
