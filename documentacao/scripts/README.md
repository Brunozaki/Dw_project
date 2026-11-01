# Pasta `scripts/`

Esta pasta guarda os scripts que preparam o ambiente. Um script é um arquivo com uma sequência de comandos, executados de uma vez.

**Por que a pasta existe:** preparar o ambiente manualmente exige muitos comandos, e um erro de digitação pode dar problema. Com os scripts, todos preparam o ambiente do mesmo jeito.

| Arquivo | Motivo de existir | Quantas vezes rodar |
|---|---|---|
| `setup-docker-wsl.sh` | Instala o Docker no Ubuntu | Uma vez por computador |
| `create-env.sh` | Cria o `.env` com senhas aleatórias | Uma vez por computador |

Os dois rodam no **terminal do Ubuntu**, na pasta do projeto. Eles não funcionam no PowerShell.

## `setup-docker-wsl.sh`

**Por que existe:** o Docker oficial não vem no Ubuntu. Instalá-lo exige adicionar o repositório da Docker e vários pacotes, e o script faz isso de forma repetível.

**Como rodar:**

```bash
sudo bash scripts/setup-docker-wsl.sh "$USER"
```

- `sudo` executa como administrador do Linux e pede sua senha.
- `"$USER"` é trocado pelo seu nome de usuário, que receberá permissão para usar o Docker.

**O que ele faz, em ordem:**

1. Confere se rodou como administrador e se o usuário existe.
2. Confere o `systemd`, o sistema que inicia os serviços do Linux. Se estiver desligado, ativa e pede para reiniciar o WSL.
3. Adiciona o repositório oficial da Docker, com sua chave de segurança.
4. Instala o Docker Engine e o Docker Compose.
5. Dá ao usuário permissão para usar o Docker.
6. Inicia o Docker e o configura para iniciar junto com o Ubuntu.
7. Roda o container de teste `hello-world` e mostra as versões instaladas.

**Por que Docker Engine, e não Docker Desktop:** o Engine consome menos recursos, fica mais parecido com um servidor Linux real e guarda imagens e dados no disco escolhido para o Ubuntu.

**Depois de rodar:** feche e abra o terminal. A permissão só vale em um novo acesso.

## `create-env.sh`

**Por que existe:** cada instalação precisa de senhas próprias e fortes. O script as gera automaticamente, sem que ninguém precise inventá-las.

**Como rodar:**

```bash
bash scripts/create-env.sh
```

**O que ele faz, em ordem:**

1. Vai para a pasta principal do projeto.
2. Para com erro se o `.env` já existir, para não apagar as senhas atuais.
3. Gera as senhas e a `FERNET_KEY`.
4. Copia o `.env.example` para `.env`, trocando cada `gerar` por um valor aleatório.

**Importante:** se o `.env` for apagado depois que os bancos existirem, as senhas novas não vão coincidir com as gravadas nos bancos. Guarde uma cópia em um local seguro, como um gerenciador de senhas.

## Como criar um script novo

1. Crie um arquivo `.sh` nesta pasta.
2. Comece com estas duas linhas. A segunda faz o script parar no primeiro erro:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

3. Adicione um comentário no início, dizendo o que ele faz e como usar.
4. Se ele for preciso na instalação, inclua-o em [Como aplicar](../como-aplicar.md).
