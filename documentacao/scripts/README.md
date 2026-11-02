# Pasta `scripts/`

Esta pasta guarda os scripts que preparam o ambiente. Um script é um arquivo com uma sequência de comandos, executados de uma vez.

**Por que a pasta existe:** preparar o ambiente manualmente exige muitos comandos, e um erro de digitação pode dar problema. Com os scripts, todos preparam o ambiente do mesmo jeito.

| Arquivo | Motivo de existir | Quantas vezes rodar |
|---|---|---|
| `setup-docker-wsl.sh` | Instala o Docker no Ubuntu | Uma vez por computador |
| `create-env.sh` | Cria o `.env` com senhas aleatórias | Uma vez por computador |
| `gerar_dados_logistica.py` | Cria dados fictícios de logística em CSV | Quando precisar dos dados ou mudar o volume |

Os dois arquivos `.sh` rodam no **terminal do Ubuntu**, na pasta do projeto. Eles não funcionam no PowerShell. O arquivo `.py` roda em qualquer sistema com Python.

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

## `gerar_dados_logistica.py`

**Por que existe:** nenhuma base pública gratuita reúne produtos, notas fiscais, prazos, valores e frete em grande volume. O script usa o TPC-H, um gerador de dados para testes de banco, como base de pedidos e itens, e simula o restante com dados do Brasil.

**Como rodar:**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/gerar_dados_logistica.py
```

Na primeira execução, o DuckDB precisa de internet para baixar a extensão do TPC-H.

| Opção | Padrão | O que faz |
|---|---|---|
| `--escala` | `1` | Define o volume. A escala 1 gera 1,5 milhão de pedidos, 6 milhões de itens e ocupa cerca de 2,2 GB |
| `--saida` | `data` | Define a pasta dos arquivos |
| `--data-corte` | `2026-11-01` | Define o que os dados tratam como hoje |

Os mesmos parâmetros e a mesma versão do DuckDB geram os mesmos arquivos. A pasta `data/` fica fora do Git, porque os arquivos são grandes e podem ser recriados.

**O que ele gera:**

| Pasta | Arquivos | Conteúdo |
|---|---|---|
| `data/tpch/` | `orders`, `lineitem`, `customer`, `part`, `partsupp`, `supplier`, `nation`, `region` | Base TPC-H original |
| `data/simulado/` | `locais`, `centros_distribuicao`, `transportadoras` | Cadastros de apoio |
| `data/simulado/` | `clientes`, `produtos` | Cadastros principais |
| `data/simulado/` | `pedidos`, `itens_pedido` | Vendas |
| `data/simulado/` | `notas_fiscais`, `entregas` | Faturamento e transporte |

O arquivo `entregas` tem origem, destino, transportadora, datas, peso e frete, os campos que a tabela `marts.fact_shipment` espera.

**Como os dados são simulados:**

- **Clientes:** são distribuídos entre 70 cidades conforme a população aproximada.
- **Origem:** cada cliente recebe do centro de distribuição mais próximo.
- **Prazo:** depende da distância e do modal. Envios e entregas não ocorrem aos domingos.
- **Atraso:** varia por transportadora e é mais provável no Norte, no Nordeste e em novembro e dezembro.
- **Frete:** usa peso real ou cubado, distância, tarifa do modal e 0,3% do valor da mercadoria.
- **Situação do pedido:** cerca de 2% são cancelados. Pedidos recentes podem aparecer como `em_transito` ou `aguardando_envio`.
- **Nota fiscal:** cada pedido faturado tem uma nota, com chave de 44 dígitos, CFOP e ICMS simplificado.

**Limitações:**

- Empresas, CNPJs, CEPs e endereços são fictícios. Os CNPJs têm dígito verificador errado de propósito, para não coincidir com os reais.
- As notas não têm valor fiscal, e as alíquotas são uma simplificação.
- O número de pedidos é quase igual em todos os meses, porque essa distribuição vem do TPC-H.
- Coordenadas e distâncias são aproximadas. A cabotagem pode aparecer para cidades sem porto.

## Como criar um script novo

1. Crie um arquivo `.sh` nesta pasta.
2. Comece com estas duas linhas. A segunda faz o script parar no primeiro erro:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

3. Adicione um comentário no início, dizendo o que ele faz e como usar.
4. Se ele for preciso na instalação, inclua-o em [Como aplicar](../como-aplicar.md).
