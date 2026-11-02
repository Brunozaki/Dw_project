# Instalação manual em um Linux limpo

Este guia instala o PostgreSQL e o Airflow diretamente em um servidor Linux, **sem Docker**. Cada comando é digitado à mão, e o guia explica o motivo de cada etapa.

Para rodar no Windows com Docker, use o guia [Como aplicar](como-aplicar.md). Os dois caminhos levam ao mesmo resultado; escolha apenas um.

| | Com Docker | Manual, neste guia |
|---|---|---|
| **Instalação** | Um comando sobe tudo | Cada parte é instalada e configurada |
| **Onde os programas ficam** | Dentro de containers | Diretamente no sistema |
| **Início automático** | Docker | `systemd`, o gerenciador de serviços do Linux |
| **Bancos de dados** | Dois servidores Postgres | Um servidor Postgres com dois bancos |
| **Atualizações** | Trocar a versão no Compose | Atualizar cada programa |
| **Melhor para** | Estudo e computador pessoal | Servidor dedicado, ou onde Docker não é permitido |

## Antes de começar

Você vai precisar de:

- **Ubuntu ou Debian** com `systemd`. Este guia foi testado no Ubuntu 26.04. Em outras versões, os comandos devem ser os mesmos, mas a versão do Postgres muda. Red Hat, Rocky e similares usam outros comandos e não estão cobertos.
- **Python 3.10 a 3.14**, que normalmente já vem no sistema. Confira com `python3 --version`.
- **4 GB de memória RAM**, no mínimo, e 8 GB é o recomendado.
- **10 GB livres em disco**, além do espaço dos dados.
- **Um usuário com permissão de `sudo`.** Se você entra como `root`, os comandos funcionam do mesmo jeito.
- **Internet** durante a instalação.

Os comandos abaixo usam blocos de várias linhas. Copie cada bloco inteiro, cole no terminal e pressione Enter.

## Etapa 1: instalar os pacotes do sistema

```bash
sudo apt update
```

```bash
sudo apt install -y postgresql python3-venv python3-dev build-essential libpq-dev git curl openssl
```

| Pacote | Para que serve |
|---|---|
| `postgresql` | O banco de dados |
| `python3-venv` | Cria um ambiente isolado para o Airflow |
| `python3-dev`, `build-essential`, `libpq-dev` | Permitem compilar bibliotecas do Python, se preciso |
| `git` | Baixa o projeto |
| `curl` | Testa os serviços pelo terminal |
| `openssl` | Gera senhas aleatórias |

Depois, deixe o Postgres ligado e configurado para iniciar com o sistema:

```bash
sudo systemctl enable --now postgresql
```

**Como saber se deu certo:** o comando abaixo mostra uma linha com `online`.

```bash
pg_lsclusters
```

## Etapa 2: gerar as senhas

Este comando cria um arquivo com as senhas, que só o seu usuário consegue ler:

```bash
cat > ~/dw-segredos.env <<EOF
AIRFLOW_DB_PASSWORD=$(openssl rand -hex 24)
DW_PASSWORD=$(openssl rand -hex 24)
AIRFLOW_ADMIN_PASSWORD=$(openssl rand -hex 24)
AIRFLOW_JWT_SECRET=$(openssl rand -hex 24)
FERNET_KEY=$(openssl rand -base64 32 | tr '+/' '-_')
EOF
chmod 600 ~/dw-segredos.env
```

Rode este comando **uma vez só**. Rodar de novo troca as senhas no arquivo, e elas deixam de coincidir com as já configuradas. Guarde uma cópia em um gerenciador de senhas.

| Valor | Para que serve |
|---|---|
| `AIRFLOW_DB_PASSWORD` | Acesso do Airflow ao seu banco interno |
| `DW_PASSWORD` | Acesso ao data warehouse |
| `AIRFLOW_ADMIN_PASSWORD` | Login no site do Airflow |
| `AIRFLOW_JWT_SECRET` | Segredo da comunicação interna do Airflow |
| `FERNET_KEY` | Chave que criptografa as senhas guardadas pelo Airflow |

## Etapa 3: criar os bancos de dados

Serão dois usuários e dois bancos: um para o Airflow e outro para o data warehouse. Assim, os dados do negócio não se misturam com os dados internos do Airflow.

```bash
source ~/dw-segredos.env
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
CREATE ROLE airflow LOGIN PASSWORD '$AIRFLOW_DB_PASSWORD';
CREATE ROLE dw_admin LOGIN PASSWORD '$DW_PASSWORD';
CREATE DATABASE airflow OWNER airflow;
CREATE DATABASE dw_logistica OWNER dw_admin;
SQL
```

**Como saber se deu certo:** aparecem duas vezes `CREATE ROLE` e duas vezes `CREATE DATABASE`.

## Etapa 4: baixar o projeto

```bash
sudo git clone https://github.com/Brunozaki/Dw_project.git /opt/dw_project
```

A pasta `/opt` é o local usual para programas instalados manualmente.

## Etapa 5: criar a estrutura do data warehouse

No Docker, os arquivos de `sql/dw` rodam sozinhos. Aqui, você os aplica uma vez, em ordem:

```bash
source ~/dw-segredos.env
for arquivo in /opt/dw_project/sql/dw/*.sql; do
  PGPASSWORD="$DW_PASSWORD" psql -h 127.0.0.1 -U dw_admin -d dw_logistica -v ON_ERROR_STOP=1 -f "$arquivo"
done
```

**Como saber se deu certo:** o comando abaixo mostra `5844`, o número de dias do calendário.

```bash
source ~/dw-segredos.env
PGPASSWORD="$DW_PASSWORD" psql -h 127.0.0.1 -U dw_admin -d dw_logistica -tc "SELECT count(*) FROM marts.dim_date;"
```

## Etapa 6: instalar o Airflow

Por segurança, o Airflow roda com um usuário próprio, sem permissão de entrar no sistema. Assim, uma falha nele não dá acesso ao restante do servidor.

```bash
sudo useradd --system --create-home --home-dir /opt/airflow --shell /usr/sbin/nologin airflow
```

Crie um ambiente Python isolado, para as bibliotecas do Airflow não interferirem nas do sistema:

```bash
sudo -u airflow python3 -m venv /opt/airflow/venv
```

```bash
sudo -u airflow /opt/airflow/venv/bin/pip install --upgrade pip
```

Agora instale o Airflow. Este passo pode levar vários minutos.

```bash
AIRFLOW_VERSION=3.3.2
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
sudo -u airflow /opt/airflow/venv/bin/pip install "apache-airflow[postgres,fab]==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
```

- `postgres` adiciona a conexão com o Postgres, usada pelas DAGs.
- `fab` adiciona a tela de login com usuário e senha.
- `--constraint` fixa as versões das dependências em uma combinação testada pelo Airflow. **Não remova:** sem ele, a instalação pode trazer bibliotecas incompatíveis.

## Etapa 7: configurar o Airflow

Este comando cria o arquivo com a configuração do Airflow:

```bash
source ~/dw-segredos.env
sudo mkdir -p /etc/airflow
sudo tee /etc/airflow/airflow.env >/dev/null <<ENV
AIRFLOW_HOME=/opt/airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__AUTH_MANAGER=airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
AIRFLOW__CORE__DAGS_FOLDER=/opt/dw_project/dags
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
AIRFLOW__CORE__DEFAULT_TIMEZONE=America/Sao_Paulo
AIRFLOW__CORE__FERNET_KEY=$FERNET_KEY
AIRFLOW__CORE__EXECUTION_API_SERVER_URL=http://localhost:8080/execution/
AIRFLOW__API_AUTH__JWT_SECRET=$AIRFLOW_JWT_SECRET
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:$AIRFLOW_DB_PASSWORD@127.0.0.1/airflow
AIRFLOW_CONN_DW_POSTGRES=postgresql://dw_admin:$DW_PASSWORD@127.0.0.1:5432/dw_logistica
DW_DATA_DIR=/opt/dw_project/data
ENV
sudo chown root:airflow /etc/airflow/airflow.env
sudo chmod 640 /etc/airflow/airflow.env
```

Como o arquivo tem senhas, só o `root` e o usuário `airflow` conseguem lê-lo.

| Configuração | Significado |
|---|---|
| `AIRFLOW_HOME` | Pasta de trabalho do Airflow |
| `EXECUTOR=LocalExecutor` | Roda as tarefas na própria máquina, sem serviços extras |
| `AUTH_MANAGER` | Usa a tela de login com usuário e senha |
| `DAGS_FOLDER` | Pasta das DAGs do projeto |
| `LOAD_EXAMPLES=False` | Não carrega as DAGs de exemplo |
| `DAGS_ARE_PAUSED_AT_CREATION=True` | Toda DAG nova começa pausada |
| `DEFAULT_TIMEZONE` | Fuso usado nos agendamentos |
| `EXECUTION_API_SERVER_URL` | Endereço pelo qual as tarefas falam com o Airflow |
| `SQL_ALCHEMY_CONN` | Conexão com o banco interno do Airflow |
| `AIRFLOW_CONN_DW_POSTGRES` | Conexão `dw_postgres`, usada pelas DAGs para acessar o DW |
| `DW_DATA_DIR` | Pasta dos arquivos gerados, lidos pela carga |

Crie também um atalho para rodar comandos do Airflow já com essa configuração:

```bash
sudo tee /usr/local/bin/airflow-dw >/dev/null <<'EOF'
#!/usr/bin/env bash
set -a
. /etc/airflow/airflow.env
set +a
cd /opt/airflow
exec /opt/airflow/venv/bin/airflow "$@"
EOF
sudo chmod 755 /usr/local/bin/airflow-dw
```

**Como saber se deu certo:** o comando abaixo mostra `3.3.2`, possivelmente depois de algumas mensagens.

```bash
sudo -u airflow airflow-dw version
```

## Etapa 8: preparar o banco do Airflow e o login

Crie as tabelas internas do Airflow:

```bash
sudo -u airflow airflow-dw db migrate
```

Crie o usuário do site:

```bash
source ~/dw-segredos.env
sudo -u airflow airflow-dw users create --username admin --firstname Admin --lastname DW --role Admin --email admin@example.com --password "$AIRFLOW_ADMIN_PASSWORD"
```

**Como saber se deu certo:** a última linha diz `User "admin" created with role "Admin"`. As muitas mensagens de `Added Permission` antes dela são normais.

## Etapa 9: criar os serviços

Os arquivos abaixo dizem ao `systemd` como iniciar cada parte do Airflow. Com eles, tudo inicia com o sistema e reinicia sozinho em caso de falha.

Site e API:

```bash
sudo tee /etc/systemd/system/airflow-apiserver.service >/dev/null <<'EOF'
[Unit]
Description=Airflow api-server
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
User=airflow
Group=airflow
WorkingDirectory=/opt/airflow
EnvironmentFile=/etc/airflow/airflow.env
ExecStart=/opt/airflow/venv/bin/airflow api-server --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Agendador, que também executa as tarefas:

```bash
sudo tee /etc/systemd/system/airflow-scheduler.service >/dev/null <<'EOF'
[Unit]
Description=Airflow scheduler
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
User=airflow
Group=airflow
WorkingDirectory=/opt/airflow
EnvironmentFile=/etc/airflow/airflow.env
ExecStart=/opt/airflow/venv/bin/airflow scheduler
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Leitor das DAGs:

```bash
sudo tee /etc/systemd/system/airflow-dag-processor.service >/dev/null <<'EOF'
[Unit]
Description=Airflow dag-processor
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
User=airflow
Group=airflow
WorkingDirectory=/opt/airflow
EnvironmentFile=/etc/airflow/airflow.env
ExecStart=/opt/airflow/venv/bin/airflow dag-processor
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

| Linha | Significado |
|---|---|
| `After` e `Requires` | Só inicia depois do Postgres e depende dele |
| `User` | Roda com o usuário `airflow`, não como `root` |
| `EnvironmentFile` | Lê a configuração da Etapa 7 |
| `ExecStart` | Comando que inicia o serviço |
| `Restart=on-failure` | Reinicia em caso de falha |
| `WantedBy` | Faz o serviço iniciar com o sistema |

O `--host 127.0.0.1` faz o site responder só dentro do servidor, o que evita expô-lo à internet. Veja como acessar em [Etapa 11](#etapa-11-entrar-no-airflow).

Ative os três serviços:

```bash
sudo systemctl daemon-reload
```

```bash
sudo systemctl enable --now airflow-apiserver airflow-scheduler airflow-dag-processor
```

## Etapa 10: verificar os serviços

Aguarde cerca de um minuto. Depois, rode:

```bash
systemctl is-active postgresql airflow-apiserver airflow-scheduler airflow-dag-processor
```

**Como saber se deu certo:** aparece `active` quatro vezes.

Depois, teste o site:

```bash
curl -s http://127.0.0.1:8080/api/v2/monitor/health
```

**Como saber se deu certo:** `metadatabase`, `scheduler` e `dag_processor` aparecem como `healthy`. O `triggerer` aparece como `null`, o que é esperado: ele não é usado neste projeto.

## Etapa 11: entrar no Airflow

Veja sua senha:

```bash
grep AIRFLOW_ADMIN_PASSWORD ~/dw-segredos.env
```

**Se o Linux está no seu computador**, abra http://localhost:8080.

**Se é um servidor remoto**, crie um túnel SSH. No **seu computador**, abra um terminal e rode o comando abaixo, trocando o usuário e o endereço. Mantenha esse terminal aberto e acesse http://localhost:8080.

```text
ssh -L 8080:127.0.0.1:8080 usuario@endereco-do-servidor
```

O túnel leva o site até você por uma conexão criptografada, sem abrir portas no servidor.

Entre com o usuário `admin` e a senha acima. O item **Disparador** em vermelho é esperado, pelo mesmo motivo do `triggerer`.

## Etapa 12: testar a automação

Você pode usar o site, como em [Como aplicar](como-aplicar.md#etapa-10-testar-a-automação), ou o terminal.

Espere a DAG aparecer. Isso pode levar um ou dois minutos:

```bash
sudo -u airflow airflow-dw dags list
```

Ative a DAG e mande rodar:

```bash
sudo -u airflow airflow-dw dags unpause dw_healthcheck
```

```bash
sudo -u airflow airflow-dw dags trigger dw_healthcheck
```

Aguarde alguns segundos e confira as execuções:

```bash
sudo -u airflow airflow-dw dags list-runs dw_healthcheck
```

**Como saber se deu certo:** as execuções aparecem como `success`, e o comando abaixo mostra pelo menos uma linha com `dw_healthcheck` e `success`.

```bash
source ~/dw-segredos.env
PGPASSWORD="$DW_PASSWORD" psql -h 127.0.0.1 -U dw_admin -d dw_logistica -c "SELECT dag_id, status, finished_at FROM audit.load_run;"
```

Mensagens sobre `graphviz` e `FileType is deprecated` nesses comandos são apenas avisos e podem ser ignoradas. O `dags unpause` pode mostrar `is_paused` como `True` mesmo tendo funcionado; o que vale é a execução aparecer como `success`.

## Etapa 13: gerar e carregar os dados

Gere os arquivos. Isso leva alguns minutos e ocupa cerca de 2,3 GB:

```bash
sudo python3 -m venv /opt/dw_project/.venv
```

```bash
sudo /opt/dw_project/.venv/bin/pip install -r /opt/dw_project/requirements.txt
```

```bash
cd /opt/dw_project && sudo .venv/bin/python scripts/gerar_dados_logistica.py
```

Ative a carga e mande rodar. A primeira carga traz todo o histórico, com cerca de 9 milhões de linhas, e leva cerca de 10 minutos:

```bash
sudo -u airflow airflow-dw dags unpause dw_carga_logistica
```

```bash
sudo -u airflow airflow-dw dags trigger dw_carga_logistica
```

**Como saber se deu certo:** o comando abaixo mostra uma linha com `dw_carga_logistica`, `success` e a quantidade de linhas carregadas.

```bash
source ~/dw-segredos.env
PGPASSWORD="$DW_PASSWORD" psql -h 127.0.0.1 -U dw_admin -d dw_logistica -c "SELECT dag_id, status, rows_loaded, finished_at FROM audit.load_run ORDER BY finished_at DESC LIMIT 3;"
```

Se chegou até aqui, o projeto está funcionando, e os serviços voltam sozinhos quando o servidor reinicia.

## Uso no dia a dia

| Quero... | Comando |
|---|---|
| Ver o estado de um serviço | `systemctl status airflow-scheduler` |
| Reiniciar o Airflow | `sudo systemctl restart airflow-apiserver airflow-scheduler airflow-dag-processor` |
| Parar o Airflow | `sudo systemctl stop airflow-apiserver airflow-scheduler airflow-dag-processor` |
| Ver mensagens de um serviço | `journalctl -u airflow-scheduler -f` |
| Ver mensagens antigas | `journalctl -u airflow-scheduler -n 100` |
| Abrir o data warehouse | `sudo -u postgres psql -d dw_logistica` |
| Listar as DAGs | `sudo -u airflow airflow-dw dags list` |
| Ver erros nas DAGs | `sudo -u airflow airflow-dw dags list-import-errors` |

Para sair das mensagens, pressione `Ctrl + C`. Para sair do banco, digite `\q`.

**Depois de alterar `/etc/airflow/airflow.env`**, reinicie o Airflow para aplicar a mudança.

**Para atualizar as DAGs do projeto:**

```bash
sudo git -C /opt/dw_project pull
```

## Cópia de segurança

Sem cópia, uma falha de disco significa perder o data warehouse. Este comando salva o banco em um arquivo:

```bash
sudo -u postgres pg_dump -Fc -f /tmp/dw_logistica.dump dw_logistica
```

Mova o arquivo para fora do servidor, porque uma cópia no mesmo disco não protege contra a perda dele.

Para restaurar em um banco `dw_logistica` vazio, depois da Etapa 3:

```bash
sudo -u postgres pg_restore -d dw_logistica /tmp/dw_logistica.dump
```

## Segurança em um servidor real

- **Não abra as portas 8080 e 5432 para a internet.** Use o túnel SSH da Etapa 11.
- **Ative o firewall liberando o SSH antes.** Sem essa ordem, você pode perder o acesso ao servidor:

```text
sudo ufw allow OpenSSH
sudo ufw enable
```

- **Proteja o arquivo `~/dw-segredos.env`.** Não o envie a outras pessoas nem o coloque no Git.
- **Mantenha o sistema atualizado** com `sudo apt update` e `sudo apt upgrade`.
- **Não use `dw_admin` em relatórios.** Crie usuários do banco só com permissão de leitura.

## Problemas comuns

| O que aparece | Causa provável | Como resolver |
|---|---|---|
| `pg_lsclusters` sem `online` | Postgres parado | Rode `sudo systemctl start postgresql` |
| `role ... already exists` | A Etapa 3 já foi feita | Siga em frente, com as senhas originais |
| `password authentication failed` | O `dw-segredos.env` foi gerado de novo | Troque a senha no banco com `ALTER ROLE` ou recupere o arquivo original |
| Erro `404` no `--constraint` | Versão do Python sem suporte | Use Python de 3.10 a 3.14 |
| `pip` falha ao compilar | Faltam pacotes da Etapa 1 | Repita a Etapa 1 e tente de novo |
| `airflow-dw: command not found` | O atalho da Etapa 7 não foi criado | Repita o bloco do atalho |
| Serviço não fica `active` | Erro na inicialização | Rode `journalctl -u nome-do-servico -n 50` |
| `Address already in use` | Outro programa usa a porta 8080 | Troque a porta em `airflow-apiserver.service` e em `EXECUTION_API_SERVER_URL` |
| DAG não aparece | Leitura pendente ou erro no arquivo | Espere dois minutos e veja `dags list-import-errors` |
| Tarefa fica em `queued` | O scheduler não está rodando | Rode `systemctl status airflow-scheduler` |
| Site não abre em servidor remoto | Túnel SSH fechado | Repita o comando do túnel e mantenha o terminal aberto |
| Serviços param no WSL | O WSL desliga sem terminal aberto | Mantenha um terminal aberto. Em servidor Linux real, isso não acontece |
