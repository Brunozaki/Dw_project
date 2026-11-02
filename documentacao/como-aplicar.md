# Como aplicar o projeto

Este guia leva um computador com Windows até o projeto funcionando. Siga as etapas na ordem e não pule a verificação no final de cada uma. Se uma etapa falhar, consulte [Problemas comuns](#problemas-comuns).

## Antes de começar

Você vai precisar de:

- Windows 10 (versão 2004 ou mais nova) ou Windows 11.
- Permissão de administrador no computador.
- Pelo menos 8 GB de memória RAM. O Airflow exige no mínimo 4 GB só para ele.
- Pelo menos 20 GB livres em disco. Se o disco `C:` estiver cheio, use outro disco, como mostrado na Etapa 3.
- Internet durante a instalação.

## Etapa 1: instalar o WSL

O WSL é o recurso do Windows que permite rodar Linux.

1. Clique com o botão direito no menu Iniciar.
2. Escolha **Terminal (Administrador)**.
3. Quando o Windows pedir permissão, clique em **Sim**.
4. Digite o comando abaixo e pressione Enter:

```powershell
wsl --install --no-distribution
```

**Como saber se deu certo:** o comando termina sem mensagem de erro.

## Etapa 2: reiniciar o computador

Use Iniciar → Ligar/Desligar → **Reiniciar**.

Não use **Desligar**. Com a Inicialização Rápida do Windows, desligar e ligar de novo não aplica a instalação.

## Etapa 3: instalar o Ubuntu

Abra o PowerShell e rode o comando abaixo. O trecho `E:\WSL\Ubuntu` é o local da instalação: troque `E:` por um disco com espaço livre.

```powershell
wsl --install -d Ubuntu --location E:\WSL\Ubuntu
```

Se aparecer a mensagem **"As alterações só terão efeito depois que o sistema for reiniciado"**, o Ubuntu **não** foi instalado, mesmo com a palavra "êxito" na tela. Reinicie o computador e rode o comando de novo.

**Como saber se deu certo:** rode o comando abaixo. O Ubuntu deve aparecer na lista, com `2` na coluna `VERSION`.

```powershell
wsl --list --verbose
```

## Etapa 4: criar o usuário do Linux

Abra o Ubuntu pelo menu Iniciar. Na primeira vez, ele pede um nome de usuário e uma senha.

- Use um nome simples, em letras minúsculas e sem espaços.
- Nada aparece na tela enquanto você digita a senha. Isso é normal.
- Guarde essa senha: ela será pedida sempre que um comando usar `sudo`.

**A partir daqui, todos os comandos são digitados no terminal do Ubuntu**, não no PowerShell.

**Como saber se deu certo:** o terminal mostra algo como `seu-usuario@computador:~$`.

## Etapa 5: baixar o projeto

Os discos do Windows aparecem no Ubuntu dentro de `/mnt`. Assim, `D:\Repositorio` vira `/mnt/d/Repositorio`.

Se o projeto ainda não está no computador, instale o Git e baixe o projeto:

```bash
sudo apt update
```

```bash
sudo apt install -y git
```

```bash
mkdir -p /mnt/d/Repositorio
```

```bash
cd /mnt/d/Repositorio
```

```bash
git clone https://github.com/Brunozaki/Dw_project.git
```

Depois, entre na pasta do projeto. Faça isso sempre que abrir um novo terminal:

```bash
cd /mnt/d/Repositorio/Dw_project
```

**Como saber se deu certo:** o comando `ls` mostra `docker-compose.yml` na lista.

## Etapa 6: instalar o Docker

```bash
sudo bash scripts/setup-docker-wsl.sh "$USER"
```

Se aparecer a mensagem **"systemd ativado"**, rode `wsl --shutdown` no PowerShell, abra o Ubuntu de novo, volte à pasta do projeto e repita o comando.

Quando terminar, **feche e abra o terminal do Ubuntu**. Sem isso, seu usuário ainda não tem permissão para usar o Docker.

**Como saber se deu certo:** volte à pasta do projeto e rode o comando abaixo. Ele deve mostrar a versão, sem erro de permissão.

```bash
docker compose version
```

## Etapa 7: criar o arquivo de configuração

```bash
bash scripts/create-env.sh
```

Esse comando cria o arquivo `.env`, com as senhas do projeto. Ele só precisa ser rodado uma vez. Nunca envie esse arquivo para outra pessoa nem para o GitHub.

**Como saber se deu certo:** aparece a mensagem `.env criado`.

## Etapa 8: subir os serviços

```bash
docker compose up -d
```

Na primeira vez, o Docker baixa os programas, o que pode levar vários minutos.

**Como saber se deu certo:** rode o comando abaixo. Todos os serviços devem aparecer como `healthy`, menos o `airflow-init`, que termina sozinho depois de preparar o Airflow.

```bash
docker compose ps
```

Se algum aparecer como `starting`, espere um minuto e rode de novo.

## Etapa 9: entrar no Airflow

1. Veja sua senha com o comando abaixo:

```bash
grep AIRFLOW_ADMIN_PASSWORD .env
```

2. No navegador, abra http://localhost:8080.
3. Entre com o usuário `admin` e a senha que apareceu.

**Como saber se deu certo:** aparece a tela de boas-vindas. O idioma segue o do seu navegador.

Na seção **Saúde**, o item **Disparador** aparece em vermelho. **Isso é normal:** ele não é usado neste projeto e foi deixado de fora de propósito. Os demais itens devem estar em verde.

## Etapa 10: testar a automação

1. No Airflow, abra a página **Dags** e clique em `dw_healthcheck`.
2. Ative a DAG no botão ao lado do nome. Toda DAG nova começa pausada.
3. Clique em **Acionar**, no canto superior direito, para rodar agora.
4. Aguarde até as tarefas ficarem verdes.

Ao ativar a DAG, o Airflow pode rodar sozinho o agendamento mais recente. Por isso, podem aparecer duas execuções em vez de uma.

**Como saber se deu certo:** rode o comando abaixo. Ele deve mostrar pelo menos uma linha com `dw_healthcheck` e `success`.

```bash
docker compose exec postgres-dw psql -U dw_admin -d dw_logistica -c "SELECT * FROM audit.load_run;"
```

Se chegou até aqui, o projeto está funcionando.

## Uso no dia a dia

Rode os comandos abaixo na pasta do projeto, no terminal do Ubuntu.

| Quero... | Comando |
|---|---|
| Ver o estado dos serviços | `docker compose ps` |
| Iniciar os serviços | `docker compose up -d` |
| Parar os serviços, mantendo os dados | `docker compose stop` |
| Ver as mensagens de um serviço | `docker compose logs -f airflow-scheduler` |
| Abrir o banco de dados | `docker compose exec postgres-dw psql -U dw_admin -d dw_logistica` |

Para sair da visualização de mensagens, pressione `Ctrl + C`. Para sair do banco de dados, digite `\q`.

**Para os serviços funcionarem, deixe um terminal do Ubuntu aberto.** Sem nenhum terminal aberto, o WSL desliga em menos de um minuto e leva todos os serviços junto. Os dados não se perdem: ao abrir o Ubuntu de novo, os serviços voltam sozinhos em cerca de um minuto. Se não voltarem, rode `docker compose up -d`.

**Para conectar um programa ao banco**, como DBeaver ou Power BI, use:

| Campo | Valor |
|---|---|
| Servidor | `localhost` |
| Porta | `5433` |
| Banco | `dw_logistica` |
| Usuário | `dw_admin` |
| Senha | o valor de `DW_PASSWORD`, no arquivo `.env` |

## Cuidados importantes

- **Mantenha o computador ligado e o Ubuntu aberto no horário da carga.** Sem isso, a carga não roda. Ao voltar, o Airflow executa apenas o agendamento mais recente que foi perdido, não todos os dias que passaram.
- **Não use `docker compose down -v` sem ter certeza.** A opção `-v` apaga os volumes e, com eles, **todos os dados do data warehouse**. Sem o `-v`, os dados são mantidos.
- **Não apague o arquivo `.env`.** As senhas dos bancos já criados estão nele. Sem o arquivo, os serviços não conseguem se conectar.

## Problemas comuns

| O que aparece | Causa provável | Como resolver |
|---|---|---|
| `wsl` diz que não está instalado | A Etapa 1 não terminou | Repita a Etapa 1 em um terminal de administrador |
| Mensagem de "reiniciado" na Etapa 3 | O reinício ainda não foi aplicado | Use **Reiniciar**, não Desligar, e repita a Etapa 3 |
| Ubuntu não aparece em `wsl --list --verbose` | A instalação não terminou | Repita a Etapa 3 e leia a mensagem final |
| Erro de virtualização | Virtualização desativada na BIOS | Ative a opção (Intel VT-x ou AMD SVM) na BIOS do computador |
| `permission denied` ao usar o Docker | O terminal não foi reaberto | Feche e abra o terminal do Ubuntu |
| `required variable ... is missing` | O arquivo `.env` não existe | Rode a Etapa 7 |
| `.env já existe` | A Etapa 7 já foi feita | Nada a fazer: o script protege as senhas atuais |
| `port is already allocated` | Outro programa usa a porta | Mude `AIRFLOW_PORT` ou `DW_PORT` no `.env` e rode `docker compose up -d` |
| Localhost não abre | O WSL desligou por falta de terminal aberto | Abra o Ubuntu, espere um minuto e tente de novo |
| Localhost continua sem abrir | Os serviços não estão prontos | Rode `docker compose ps` e veja se estão `healthy` |
| **Disparador** em vermelho no Airflow | Serviço não usado neste projeto | Nada a fazer: é o comportamento esperado |
| Serviço como `unhealthy` | Erro no serviço | Rode `docker compose logs nome-do-servico` e leia as últimas linhas |
| DAG não aparece no Airflow | Erro no arquivo ou leitura pendente | Espere alguns minutos e veja `docker compose logs airflow-dag-processor` |
| Tabelas não existem no banco | O volume foi criado antes dos arquivos SQL | Veja [Como alterar as tabelas](sql/dw/README.md#como-alterar-as-tabelas) |
