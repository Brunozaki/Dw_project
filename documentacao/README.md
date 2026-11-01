# Documentação do projeto

Esta pasta explica o projeto para quem nunca teve contato com ele. Você não precisa de nenhuma ferramenta de IA para acompanhar: basta seguir os guias na ordem indicada.

## O que é este projeto

É um **data warehouse** de logística, ou seja, um banco de dados feito para análise. Ele reúne dados de várias origens em um só lugar e é atualizado automaticamente todos os dias.

Quatro tecnologias fazem isso funcionar:

| Tecnologia | Para que serve neste projeto |
|---|---|
| **Linux (Ubuntu no WSL)** | Sistema onde tudo roda. O WSL permite usar Linux dentro do Windows, sem um servidor. |
| **Docker** | Roda cada programa em um "container", um ambiente isolado que funciona igual em qualquer máquina. |
| **PostgreSQL** | Banco de dados. É onde os dados do data warehouse ficam guardados. |
| **Airflow** | Agendador. Executa as tarefas de carga nos horários definidos e mostra se deram certo. |

## Por onde começar

1. Leia o guia [Como aplicar](como-aplicar.md). Ele leva do computador vazio até o projeto funcionando.
2. Quando quiser entender ou alterar algo, consulte o guia da pasta correspondente.

## Guias por pasta

A documentação segue a mesma organização do projeto:

| Pasta do projeto | Guia | O que explica |
|---|---|---|
| Raiz (pasta principal) | [raiz/README.md](raiz/README.md) | Arquivos de configuração e o porquê de cada um |
| `dags/` | [dags/README.md](dags/README.md) | Tarefas automáticas do Airflow |
| `scripts/` | [scripts/README.md](scripts/README.md) | Scripts que preparam o ambiente |
| `sql/dw/` | [sql/dw/README.md](sql/dw/README.md) | Estrutura do banco de dados |

## Palavras usadas nos guias

| Termo | Significado |
|---|---|
| **Terminal** | Janela onde você digita comandos. |
| **Container** | Programa rodando isolado dentro do Docker. |
| **Volume** | Área de disco do Docker onde os dados ficam guardados, mesmo que o container seja apagado. |
| **DAG** | Conjunto de tarefas do Airflow e a ordem em que elas rodam. |
| **Schema** | Divisão interna do banco de dados, parecida com uma pasta para tabelas. |
| **Tabela fato** | Tabela que guarda os acontecimentos, como cada entrega realizada. |
| **Tabela dimensão** | Tabela que descreve os acontecimentos, como quem transportou e para onde foi. |
| **Modelo estrela** | Organização com uma tabela fato no centro, ligada às tabelas dimensão. |
