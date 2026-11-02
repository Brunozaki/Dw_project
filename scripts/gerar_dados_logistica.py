#!/usr/bin/env python3
"""Gera dados fictícios de logística no Brasil, em CSV, a partir do TPC-H.

Uso: python scripts/gerar_dados_logistica.py [--escala 1] [--saida data]
         [--data-corte 2026-11-01] [--dias-lote 365]

O TPC-H define o volume e a estrutura de pedidos e itens. Os demais dados são
simulados: o mesmo comando, com os mesmos parâmetros, gera os mesmos arquivos.

A pasta simulado/ é a foto da operação na data de corte. A pasta lotes/ traz, para
cada dia seguinte, o que mudou nesse dia, como uma exportação diária do sistema de origem.
"""
import argparse
import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import duckdb

# cidade, UF, latitude, longitude, população aproximada (mil), início do CEP
CIDADES = [
    ("Rio Branco", "AC", -9.97, -67.81, 364, "699"),
    ("Maceió", "AL", -9.65, -35.71, 958, "570"),
    ("Manaus", "AM", -3.12, -60.02, 2063, "690"),
    ("Macapá", "AP", 0.03, -51.07, 442, "689"),
    ("Salvador", "BA", -12.97, -38.50, 2418, "400"),
    ("Feira de Santana", "BA", -12.27, -38.97, 616, "440"),
    ("Camaçari", "BA", -12.70, -38.32, 300, "428"),
    ("Vitória da Conquista", "BA", -14.86, -40.84, 370, "450"),
    ("Fortaleza", "CE", -3.73, -38.52, 2428, "600"),
    ("Juazeiro do Norte", "CE", -7.21, -39.32, 286, "630"),
    ("Brasília", "DF", -15.79, -47.88, 2817, "700"),
    ("Vitória", "ES", -20.32, -40.34, 322, "290"),
    ("Serra", "ES", -20.13, -40.31, 520, "291"),
    ("Goiânia", "GO", -16.69, -49.26, 1437, "740"),
    ("Anápolis", "GO", -16.33, -48.95, 398, "750"),
    ("São Luís", "MA", -2.53, -44.30, 1037, "650"),
    ("Imperatriz", "MA", -5.53, -47.49, 273, "659"),
    ("Belo Horizonte", "MG", -19.92, -43.94, 2315, "300"),
    ("Uberlândia", "MG", -18.92, -48.28, 713, "384"),
    ("Contagem", "MG", -19.93, -44.05, 621, "321"),
    ("Juiz de Fora", "MG", -21.76, -43.35, 540, "360"),
    ("Extrema", "MG", -22.85, -46.32, 53, "375"),
    ("Montes Claros", "MG", -16.73, -43.86, 414, "394"),
    ("Campo Grande", "MS", -20.44, -54.65, 898, "790"),
    ("Dourados", "MS", -22.22, -54.81, 243, "798"),
    ("Cuiabá", "MT", -15.60, -56.10, 650, "780"),
    ("Rondonópolis", "MT", -16.47, -54.64, 244, "787"),
    ("Belém", "PA", -1.46, -48.50, 1303, "660"),
    ("Santarém", "PA", -2.44, -54.71, 331, "680"),
    ("Marabá", "PA", -5.37, -49.12, 266, "685"),
    ("João Pessoa", "PB", -7.12, -34.86, 833, "580"),
    ("Campina Grande", "PB", -7.23, -35.88, 419, "581"),
    ("Recife", "PE", -8.05, -34.88, 1488, "500"),
    ("Cabo de Santo Agostinho", "PE", -8.29, -35.03, 203, "545"),
    ("Caruaru", "PE", -8.28, -35.98, 378, "550"),
    ("Petrolina", "PE", -9.39, -40.50, 386, "563"),
    ("Teresina", "PI", -5.09, -42.80, 866, "640"),
    ("Curitiba", "PR", -25.43, -49.27, 1773, "800"),
    ("São José dos Pinhais", "PR", -25.53, -49.21, 329, "830"),
    ("Londrina", "PR", -23.31, -51.16, 555, "860"),
    ("Maringá", "PR", -23.42, -51.94, 409, "870"),
    ("Cascavel", "PR", -24.96, -53.46, 348, "858"),
    ("Rio de Janeiro", "RJ", -22.91, -43.17, 6211, "200"),
    ("Duque de Caxias", "RJ", -22.79, -43.31, 808, "250"),
    ("Niterói", "RJ", -22.88, -43.10, 481, "240"),
    ("Campos dos Goytacazes", "RJ", -21.75, -41.32, 483, "280"),
    ("Natal", "RN", -5.79, -35.21, 751, "590"),
    ("Mossoró", "RN", -5.19, -37.34, 264, "596"),
    ("Porto Velho", "RO", -8.76, -63.90, 460, "768"),
    ("Boa Vista", "RR", 2.82, -60.67, 413, "693"),
    ("Porto Alegre", "RS", -30.03, -51.23, 1332, "900"),
    ("Gravataí", "RS", -29.94, -50.99, 265, "940"),
    ("Caxias do Sul", "RS", -29.17, -51.18, 463, "950"),
    ("Pelotas", "RS", -31.77, -52.34, 325, "960"),
    ("Florianópolis", "SC", -27.60, -48.55, 537, "880"),
    ("Joinville", "SC", -26.30, -48.85, 616, "892"),
    ("Blumenau", "SC", -26.92, -49.07, 361, "890"),
    ("Chapecó", "SC", -27.10, -52.62, 254, "898"),
    ("Aracaju", "SE", -10.91, -37.07, 602, "490"),
    ("São Paulo", "SP", -23.55, -46.63, 11452, "010"),
    ("Cajamar", "SP", -23.36, -46.88, 92, "077"),
    ("Guarulhos", "SP", -23.46, -46.53, 1291, "070"),
    ("Campinas", "SP", -22.91, -47.06, 1139, "130"),
    ("Ribeirão Preto", "SP", -21.18, -47.81, 698, "140"),
    ("São José dos Campos", "SP", -23.19, -45.88, 697, "122"),
    ("Santos", "SP", -23.96, -46.33, 418, "110"),
    ("Sorocaba", "SP", -23.50, -47.46, 723, "180"),
    ("São José do Rio Preto", "SP", -20.82, -49.38, 480, "150"),
    ("Bauru", "SP", -22.31, -49.06, 379, "170"),
    ("Palmas", "TO", -10.18, -48.33, 303, "770"),
]

# UF, código IBGE, região
ESTADOS = [
    ("AC", "12", "Norte"), ("AL", "27", "Nordeste"), ("AM", "13", "Norte"),
    ("AP", "16", "Norte"), ("BA", "29", "Nordeste"), ("CE", "23", "Nordeste"),
    ("DF", "53", "Centro-Oeste"), ("ES", "32", "Sudeste"), ("GO", "52", "Centro-Oeste"),
    ("MA", "21", "Nordeste"), ("MG", "31", "Sudeste"), ("MS", "50", "Centro-Oeste"),
    ("MT", "51", "Centro-Oeste"), ("PA", "15", "Norte"), ("PB", "25", "Nordeste"),
    ("PE", "26", "Nordeste"), ("PI", "22", "Nordeste"), ("PR", "41", "Sul"),
    ("RJ", "33", "Sudeste"), ("RN", "24", "Nordeste"), ("RO", "11", "Norte"),
    ("RR", "14", "Norte"), ("RS", "43", "Sul"), ("SC", "42", "Sul"),
    ("SE", "28", "Nordeste"), ("SP", "35", "Sudeste"), ("TO", "17", "Norte"),
]

# código, nome, cidade
CENTROS_DISTRIBUICAO = [
    ("CD-CAJ", "CD Cajamar", "Cajamar"),
    ("CD-EXT", "CD Extrema", "Extrema"),
    ("CD-DQC", "CD Duque de Caxias", "Duque de Caxias"),
    ("CD-SJP", "CD São José dos Pinhais", "São José dos Pinhais"),
    ("CD-GRV", "CD Gravataí", "Gravataí"),
    ("CD-ANA", "CD Anápolis", "Anápolis"),
    ("CD-CAM", "CD Camaçari", "Camaçari"),
    ("CD-CSA", "CD Cabo de Santo Agostinho", "Cabo de Santo Agostinho"),
    ("CD-MAO", "CD Manaus", "Manaus"),
]

# modal, km/dia, dias de manuseio, R$/kg/km, frete mínimo, chance de escolha
MODAIS = [
    ("Rodoviário", 600, 1, 0.0012, 45.0, 0.62),
    ("Rodoviário expresso", 900, 0, 0.0020, 70.0, 0.15),
    ("Postal", 1000, 2, 0.0040, 28.0, 0.10),
    ("Aéreo", 2500, 1, 0.0065, 120.0, 0.06),
    ("Cabotagem", 250, 4, 0.0005, 350.0, 0.04),
    ("Ferroviário", 350, 3, 0.0006, 300.0, 0.03),
]

# código, nome, modal, fator de preço, chance base de atraso
TRANSPORTADORAS = [
    ("TR-001", "Rota Serena Logística", "Rodoviário", 1.00, 0.07),
    ("TR-002", "Ipê Amarelo Cargas", "Rodoviário", 0.92, 0.13),
    ("TR-003", "Cerrado Dourado Transportes", "Rodoviário", 0.96, 0.10),
    ("TR-004", "Mandacaru Forte Logística", "Rodoviário", 0.90, 0.16),
    ("TR-005", "Boiúna Transportes Fluviais e Rodoviários", "Rodoviário", 1.08, 0.09),
    ("TR-006", "Jatobá Ligeiro Express", "Rodoviário expresso", 1.05, 0.05),
    ("TR-007", "Sabiá Veloz Encomendas", "Rodoviário expresso", 0.97, 0.09),
    ("TR-008", "Postal Beija-Flor", "Postal", 1.00, 0.11),
    ("TR-009", "Céu Aberto Cargas Aéreas", "Aéreo", 1.00, 0.04),
    ("TR-010", "Maré Mansa Cabotagem", "Cabotagem", 1.00, 0.12),
    ("TR-011", "Trilho Longo Ferrovias", "Ferroviário", 1.00, 0.10),
]

# categoria, tipo, preço mínimo, preço máximo, peso mínimo (kg), peso máximo (kg)
TIPOS_PRODUTO = [
    ("Alimentos", "Arroz tipo 1 fardo 30 kg", 95, 160, 30, 31),
    ("Alimentos", "Feijão carioca fardo 30 kg", 120, 210, 30, 31),
    ("Alimentos", "Óleo de soja caixa 20 unidades", 110, 190, 18, 19),
    ("Alimentos", "Café torrado caixa 10 kg", 180, 320, 10, 11),
    ("Bebidas", "Água mineral fardo 12 unidades", 18, 32, 18, 19),
    ("Bebidas", "Suco integral caixa 12 unidades", 70, 130, 13, 14),
    ("Higiene", "Sabonete caixa 72 unidades", 75, 130, 7, 8),
    ("Higiene", "Papel higiênico fardo 64 rolos", 60, 115, 5, 6),
    ("Limpeza", "Detergente caixa 24 unidades", 40, 72, 12, 13),
    ("Limpeza", "Sabão em pó caixa 12 kg", 75, 140, 12, 13),
    ("Eletrodomésticos", "Geladeira frost free", 2100, 4800, 42, 75),
    ("Eletrodomésticos", "Fogão 5 bocas", 780, 2300, 26, 48),
    ("Eletrodomésticos", "Lavadora de roupas", 1500, 3700, 30, 65),
    ("Eletrodomésticos", "Micro-ondas", 480, 1250, 10, 18),
    ("Eletroportáteis", "Liquidificador", 110, 340, 2, 4),
    ("Eletroportáteis", "Air fryer", 260, 780, 4, 7),
    ("Eletroportáteis", "Ventilador de coluna", 150, 430, 4, 8),
    ("Informática", "Notebook", 2300, 7200, 1.5, 3),
    ("Informática", "Monitor LED", 620, 2300, 3, 8),
    ("Informática", "Impressora multifuncional", 620, 2200, 5, 11),
    ("Celulares", "Smartphone", 820, 5200, 0.2, 0.3),
    ("Celulares", "Fone sem fio", 80, 620, 0.1, 0.3),
    ("Móveis", "Guarda-roupa 6 portas", 780, 2600, 60, 130),
    ("Móveis", "Sofá 3 lugares", 1100, 3600, 40, 85),
    ("Móveis", "Cadeira de escritório", 320, 1400, 10, 20),
    ("Construção", "Cimento paletizado 50 kg", 34, 52, 50, 51),
    ("Construção", "Argamassa saco 20 kg", 14, 30, 20, 21),
    ("Construção", "Tinta acrílica lata 18 L", 190, 520, 24, 27),
    ("Construção", "Furadeira de impacto", 170, 690, 2, 4),
    ("Autopeças", "Pneu aro 15", 280, 780, 8, 11),
    ("Autopeças", "Bateria automotiva 60 Ah", 330, 690, 13, 17),
    ("Autopeças", "Óleo de motor caixa 12 L", 240, 490, 11, 12),
    ("Farmácia", "Álcool em gel caixa 12 unidades", 75, 150, 6, 7),
    ("Farmácia", "Fralda descartável fardo", 70, 140, 3, 5),
    ("Papelaria", "Papel sulfite caixa 10 resmas", 190, 340, 23, 24),
    ("Papelaria", "Caderno universitário caixa 24", 120, 260, 12, 13),
    ("Vestuário", "Camiseta caixa 50 unidades", 620, 1600, 9, 12),
    ("Vestuário", "Calçado esportivo caixa 12 pares", 980, 3100, 9, 14),
]

MARCAS = [
    "Aurora", "Bromélia", "Capivara", "Dunas", "Esteio", "Figueira", "Guará", "Horizonte",
    "Jacarandá", "Lagoa Azul", "Maracá", "Nascente", "Oiti", "Pitanga", "Quaresmeira", "Tucano",
]
SOBRENOMES = [
    "Almeida", "Andrade", "Araújo", "Barbosa", "Barros", "Batista", "Borges", "Cardoso",
    "Carvalho", "Castro", "Cavalcante", "Costa", "Cunha", "Dias", "Duarte", "Farias",
    "Fernandes", "Ferreira", "Freitas", "Gomes", "Lima", "Lopes", "Machado", "Marques",
    "Martins", "Medeiros", "Melo", "Mendes", "Monteiro", "Moraes", "Moreira", "Moura",
    "Nascimento", "Nogueira", "Nunes", "Oliveira", "Pereira", "Pinto", "Ramos", "Reis",
    "Ribeiro", "Rocha", "Rodrigues", "Santana", "Santos", "Silva", "Soares", "Souza",
    "Teixeira", "Vieira",
]
RAMOS = [
    "Mercado", "Atacado", "Farmácia", "Materiais de Construção", "Autopeças", "Magazine",
    "Papelaria", "Comercial", "Distribuidora", "Móveis", "Informática",
]
LOGRADOUROS = [
    "Rua das Acácias", "Rua dos Ipês", "Avenida das Palmeiras", "Rua da Paz",
    "Avenida Brasil", "Rua Sete de Setembro", "Rua XV de Novembro", "Avenida Central",
    "Rua do Comércio", "Rua das Flores", "Rua Tiradentes", "Avenida Beira-Rio",
    "Rua das Laranjeiras", "Avenida da Saudade", "Rua do Porto", "Rua Boa Vista",
]
OCORRENCIAS = [
    "Destinatário ausente", "Endereço não localizado", "Avaria na carga",
    "Atraso na transferência", "Veículo com defeito", "Restrição de circulação",
]


def lista_sql(valores):
    return "[" + ", ".join("'" + v.replace("'", "''") + "'" for v in valores) + "]"


def criar_tabela(con, nome, colunas, linhas):
    marcadores = ", ".join("?" for _ in colunas.split(", "))
    con.execute(f"CREATE TABLE {nome} ({colunas})")
    con.executemany(f"INSERT INTO {nome} VALUES ({marcadores})", linhas)


def exportar(con, consulta, arquivo):
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({consulta}) TO '{arquivo.as_posix()}' (HEADER, DELIMITER ',')")
    linhas = con.execute(f"SELECT count(*) FROM ({consulta})").fetchone()[0]
    print(f"{arquivo}: {linhas:,} linhas".replace(",", "."))


def exportar_lotes(con, consulta, pasta):
    pasta.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({consulta}) TO '{pasta.as_posix()}' (FORMAT CSV, HEADER, PARTITION_BY (data_lote))")
    linhas = con.execute(f"SELECT count(*) FROM ({consulta})").fetchone()[0]
    print(f"{pasta}: {linhas:,} linhas".replace(",", "."))


def criar_referencias(con):
    criar_tabela(
        con, "ref_cidade", "cidade VARCHAR, uf VARCHAR, lat DOUBLE, lon DOUBLE, pop INTEGER, cep3 VARCHAR", CIDADES
    )
    criar_tabela(con, "ref_estado", "uf VARCHAR, cuf VARCHAR, regiao VARCHAR", ESTADOS)
    criar_tabela(con, "ref_cd", "codigo VARCHAR, nome VARCHAR, cidade VARCHAR", CENTROS_DISTRIBUICAO)
    criar_tabela(
        con,
        "ref_modal",
        "modal VARCHAR, km_dia INTEGER, manuseio INTEGER, tarifa DOUBLE, minimo DOUBLE, chance DOUBLE",
        MODAIS,
    )
    criar_tabela(
        con,
        "ref_transportadora",
        "codigo VARCHAR, nome VARCHAR, modal VARCHAR, fator_preco DOUBLE, chance_atraso DOUBLE",
        TRANSPORTADORAS,
    )
    criar_tabela(
        con,
        "ref_tipo",
        "categoria VARCHAR, tipo VARCHAR, preco_min DOUBLE, preco_max DOUBLE, peso_min DOUBLE, peso_max DOUBLE",
        TIPOS_PRODUTO,
    )
    con.execute("""
        -- Número pseudoaleatório entre 0 e 1, sempre igual para o mesmo sal e chave.
        CREATE MACRO u(sal, chave) AS (hash(sal, chave) % 1000000007) / 1000000007.0;
        CREATE MACRO escolher(lista, sal, chave) AS lista[1 + (hash(sal, chave) % len(lista))::INTEGER];

        -- Dígito verificador em módulo 11, usado no CNPJ e na chave da NF-e.
        CREATE MACRO soma_dv(s) AS list_sum(
            [substr(s, (length(s) - i)::INTEGER, 1)::INTEGER * (2 + i % 8) for i in range(length(s))]
        );
        CREATE MACRO dv(s) AS CASE WHEN soma_dv(s) % 11 < 2 THEN 0 ELSE 11 - soma_dv(s) % 11 END;

        -- O primeiro dígito verificador é errado de propósito: o CNPJ nunca coincide com um real.
        CREATE MACRO cnpj_ficticio(raiz, filial) AS
            raiz || lpad(filial::VARCHAR, 4, '0')
            || ((dv(raiz || lpad(filial::VARCHAR, 4, '0')) + 1) % 10)::VARCHAR
            || (hash('cnpj', raiz, filial) % 10)::VARCHAR;

        CREATE MACRO distancia_km(lat1, lon1, lat2, lon2) AS 6371 * 2 * asin(sqrt(
            pow(sin(radians(lat2 - lat1) / 2), 2)
            + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(radians(lon2 - lon1) / 2), 2)
        ));
        CREATE MACRO sem_domingo(d) AS CASE WHEN dayofweek(d) = 0 THEN d + 1 ELSE d END;
        CREATE MACRO status_em(cancelado, data_envio, data_entrega, dia) AS CASE
            WHEN cancelado THEN 'cancelado'
            WHEN data_envio > dia THEN 'aguardando_envio'
            WHEN data_entrega > dia THEN 'em_transito'
            ELSE 'entregue'
        END;
    """)
    con.execute("""
        CREATE TABLE locais AS
        SELECT 'LOC-' || lpad(row_number() OVER (ORDER BY c.uf, c.cidade)::VARCHAR, 3, '0') AS codigo,
               c.cidade, c.uf, e.regiao, 'BR' AS pais, c.lat, c.lon, c.pop, c.cep3, e.cuf
        FROM ref_cidade c JOIN ref_estado e USING (uf);

        CREATE TABLE centros AS
        SELECT r.codigo, r.nome, l.codigo AS codigo_local, l.cidade, l.uf, l.regiao, l.lat, l.lon, l.cuf,
               cnpj_ficticio('98000000', row_number() OVER (ORDER BY r.codigo)) AS cnpj
        FROM ref_cd r JOIN locais l USING (cidade);

        CREATE TABLE transportadoras AS
        SELECT *, cnpj_ficticio((97000000 + row_number() OVER (ORDER BY codigo))::VARCHAR, 1) AS cnpj,
               row_number() OVER (PARTITION BY modal ORDER BY codigo) - 1 AS ordem,
               count(*) OVER (PARTITION BY modal) AS total_modal
        FROM ref_transportadora;
    """)


def criar_cadastros(con):
    con.execute(f"""
        CREATE TABLE faixa_cidade AS
        SELECT *,
               coalesce(sum(pop) OVER (ORDER BY codigo ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) * 1.0
               / sum(pop) OVER () AS faixa_de,
               sum(pop) OVER (ORDER BY codigo) * 1.0 / sum(pop) OVER () AS faixa_ate
        FROM locais;

        CREATE TABLE clientes AS
        WITH base AS (
            SELECT c_custkey AS chave, u('cidade', c_custkey) AS sorteio FROM customer
        )
        SELECT b.chave,
               'CLI-' || lpad(b.chave::VARCHAR, 7, '0') AS codigo,
               escolher({lista_sql(RAMOS)}, 'nome', b.chave) AS prefixo,
               escolher({lista_sql(SOBRENOMES)}, 'sobrenome1', b.chave) || ' '
               || escolher({lista_sql(SOBRENOMES)}, 'sobrenome2', b.chave) AS sobrenomes,
               cnpj_ficticio((90000000 + b.chave)::VARCHAR, 1) AS cnpj,
               escolher({lista_sql(LOGRADOUROS)}, 'rua', b.chave) AS logradouro,
               (1 + hash('numero', b.chave) % 3999)::INTEGER AS numero,
               f.codigo AS codigo_local, f.cidade, f.uf, f.regiao, f.lat, f.lon,
               f.cep3 || lpad((hash('cep', b.chave) % 100000)::VARCHAR, 5, '0') AS cep
        FROM base b
        JOIN faixa_cidade f ON b.sorteio >= f.faixa_de AND b.sorteio < f.faixa_ate;

        CREATE TABLE produtos AS
        WITH tipos AS (SELECT *, row_number() OVER () - 1 AS indice FROM ref_tipo),
        base AS (
            SELECT p_partkey AS chave, hash('tipo', p_partkey) % (SELECT count(*) FROM tipos) AS indice
            FROM part
        )
        SELECT b.chave,
               'PRD-' || lpad(b.chave::VARCHAR, 7, '0') AS codigo,
               t.tipo || ' ' || escolher({lista_sql(MARCAS)}, 'marca', b.chave)
               || ' modelo ' || (100 + hash('modelo', b.chave) % 900)::VARCHAR AS descricao,
               t.categoria,
               escolher({lista_sql(MARCAS)}, 'marca', b.chave) AS marca,
               round(t.preco_min + u('preco', b.chave) * (t.preco_max - t.preco_min), 2)::DECIMAL(12, 2) AS preco_unitario,
               round(t.peso_min + u('peso', b.chave) * (t.peso_max - t.peso_min), 3)::DECIMAL(10, 3) AS peso_kg,
               -- Densidade entre 150 e 400 kg/m³.
               round((t.peso_min + u('peso', b.chave) * (t.peso_max - t.peso_min))
                     / (150 + u('densidade', b.chave) * 250), 4)::DECIMAL(10, 4) AS volume_m3
        FROM base b JOIN tipos t USING (indice);
    """)
    con.execute("""
        CREATE TABLE cliente_cd AS
        SELECT DISTINCT ON (c.chave) c.chave AS chave_cliente, d.codigo AS codigo_cd,
               1.25 * distancia_km(c.lat, c.lon, d.lat, d.lon) + 15 AS distancia_km
        FROM clientes c CROSS JOIN centros d
        ORDER BY c.chave, distancia_km(c.lat, c.lon, d.lat, d.lon);
    """)


def criar_movimento(con, horizonte):
    con.execute("""
        CREATE TABLE itens AS
        SELECT l.l_orderkey AS chave_pedido,
               l.l_linenumber AS numero_item,
               p.codigo AS codigo_produto,
               ceil(l.l_quantity / 5)::INTEGER AS quantidade,
               p.preco_unitario,
               l.l_discount::DECIMAL(4, 2) AS desconto_pct,
               round(ceil(l.l_quantity / 5) * p.preco_unitario, 2)::DECIMAL(14, 2) AS valor_bruto,
               round(ceil(l.l_quantity / 5) * p.preco_unitario * l.l_discount, 2)::DECIMAL(14, 2) AS valor_desconto,
               round(ceil(l.l_quantity / 5) * p.peso_kg, 3)::DECIMAL(12, 3) AS peso_kg,
               round(ceil(l.l_quantity / 5) * p.volume_m3, 4)::DECIMAL(12, 4) AS volume_m3
        FROM lineitem l JOIN produtos p ON p.chave = l.l_partkey;
    """)

    con.execute(f"""
        CREATE TABLE pedidos_base AS
        WITH deslocamento AS (
            SELECT (DATE '{horizonte}' - 1 - max(o_orderdate))::INTEGER AS dias FROM orders
        ),
        totais AS (
            SELECT chave_pedido, sum(valor_bruto) AS valor_produtos, sum(valor_desconto) AS valor_desconto,
                   sum(peso_kg) AS peso_kg, sum(volume_m3) AS volume_m3
            FROM itens GROUP BY chave_pedido
        ),
        sorteio AS (
            SELECT o.o_orderkey AS chave, u('modal', o.o_orderkey) AS s
            FROM orders o
        ),
        faixas AS (
            SELECT modal, sum(chance) OVER (ORDER BY modal ROWS UNBOUNDED PRECEDING) AS ate FROM ref_modal
        ),
        modal_sorteado AS (
            SELECT DISTINCT ON (s.chave) s.chave, f.modal
            FROM sorteio s JOIN faixas f ON s.s <= f.ate ORDER BY s.chave, f.ate
        )
        SELECT o.o_orderkey AS chave,
               'PED-' || lpad(o.o_orderkey::VARCHAR, 9, '0') AS codigo,
               o.o_custkey AS chave_cliente,
               o.o_orderdate + (SELECT dias FROM deslocamento) AS data_pedido,
               t.valor_produtos, t.valor_desconto, t.peso_kg, t.volume_m3,
               c.codigo AS codigo_cliente, c.codigo_local AS local_destino, c.uf AS uf_destino,
               c.regiao AS regiao_destino, c.cnpj AS cnpj_cliente,
               cc.codigo_cd, cc.distancia_km,
               -- Limites físicos de cada modal: peso, distância e existência de rota.
               CASE
                   WHEN m.modal = 'Postal' AND t.peso_kg > 30 THEN 'Rodoviário'
                   WHEN m.modal = 'Aéreo' AND t.peso_kg > 300 THEN 'Rodoviário expresso'
                   WHEN m.modal IN ('Cabotagem', 'Ferroviário') AND cc.distancia_km < 800 THEN 'Rodoviário'
                   ELSE m.modal
               END AS modal,
               -- Peso cubado padrão de 300 kg/m³.
               greatest(t.peso_kg, t.volume_m3 * 300) AS peso_taxado,
               CASE WHEN u('tipo_frete', o.o_orderkey) < 0.15 THEN 'FOB' ELSE 'CIF' END AS tipo_frete
        FROM orders o
        JOIN totais t ON t.chave_pedido = o.o_orderkey
        JOIN clientes c ON c.chave = o.o_custkey
        JOIN cliente_cd cc ON cc.chave_cliente = o.o_custkey
        JOIN modal_sorteado m ON m.chave = o.o_orderkey;

        CREATE TABLE pedidos_prazo AS
        WITH transporte AS (
            SELECT p.*, t.codigo AS codigo_transportadora,
                   t.chance_atraso, t.fator_preco, m.km_dia, m.manuseio, m.tarifa, m.minimo,
                   sem_domingo(p.data_pedido + 1 + (hash('envio', p.chave) % 3)::INTEGER) AS data_envio
            FROM pedidos_base p
            JOIN ref_modal m USING (modal)
            JOIN transportadoras t ON t.modal = p.modal AND t.ordem = hash('transportadora', p.chave) % t.total_modal
        ),
        prazo AS (
            SELECT *,
                   (ceil(distancia_km / km_dia) + manuseio)::INTEGER AS dias_transito,
                   sem_domingo(data_envio + (ceil(distancia_km / km_dia) + manuseio)::INTEGER
                               + 1 + (hash('folga', chave) % 2)::INTEGER) AS data_previsao,
                   -- Atraso mais provável na região Norte, no Nordeste e no fim de ano.
                   u('atraso', chave) < least(0.6, chance_atraso
                       + CASE regiao_destino WHEN 'Norte' THEN 0.09 WHEN 'Nordeste' THEN 0.03 ELSE 0 END
                       + CASE WHEN month(data_envio) IN (11, 12) THEN 0.07 ELSE 0 END) AS atrasou
            FROM transporte
        )
        SELECT *,
               sem_domingo(greatest(data_envio + 1, CASE
                   WHEN atrasou THEN data_previsao + 1 + least(30, floor(-ln(1 - u('dias_atraso', chave)) * 2.2))::INTEGER
                   ELSE data_previsao - (hash('adianto', chave) % 3)::INTEGER
               END)) AS data_entrega_simulada,
               round(greatest(minimo, peso_taxado * distancia_km * tarifa) * fator_preco
                     + (valor_produtos - valor_desconto) * 0.003, 2)::DECIMAL(14, 2) AS valor_frete
        FROM prazo;

        CREATE TABLE pedidos AS
        SELECT *, u('cancelado', chave) < 0.02 AS cancelado FROM pedidos_prazo;
    """)

    con.execute("""
        CREATE TABLE notas AS
        WITH emitidas AS (
            SELECT p.*, d.cnpj AS cnpj_emitente, d.uf AS uf_origem, d.regiao AS regiao_origem, d.cuf,
                   row_number() OVER (PARTITION BY p.codigo_cd ORDER BY p.data_envio, p.chave) AS numero
            FROM pedidos p JOIN centros d ON d.codigo = p.codigo_cd
            WHERE NOT p.cancelado
        ),
        chaves AS (
            SELECT *,
                   cuf || strftime(data_envio, '%y%m') || cnpj_emitente || '55' || '001'
                   || lpad(numero::VARCHAR, 9, '0') || '1'
                   || lpad((hash('cnf', chave) % 100000000)::VARCHAR, 8, '0') AS chave_sem_dv,
                   CASE
                       WHEN uf_origem = uf_destino THEN 18
                       WHEN regiao_origem IN ('Sul', 'Sudeste') AND uf_origem <> 'ES'
                            AND (regiao_destino IN ('Norte', 'Nordeste', 'Centro-Oeste') OR uf_destino = 'ES') THEN 7
                       ELSE 12
                   END AS aliquota_icms
            FROM emitidas
        )
        SELECT *, chave_sem_dv || dv(chave_sem_dv)::VARCHAR AS chave_nfe FROM chaves;
    """)


def exportar_tpch(con, saida):
    for tabela in ("customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"):
        exportar(con, f"SELECT * FROM {tabela}", saida / "tpch" / f"{tabela}.csv")


def criar_estados(con, data_corte, horizonte):
    """Define quais pedidos entram na foto e em cada lote diário."""
    con.execute(f"""
        CREATE TABLE estado_foto AS
        SELECT chave, DATE '{data_corte}' AS data_lote, true AS foto
        FROM pedidos WHERE data_pedido <= DATE '{data_corte}';

        CREATE TABLE estado_lotes AS
        WITH eventos AS (
            SELECT chave, data_pedido AS dia FROM pedidos
            UNION
            SELECT chave, data_envio FROM pedidos WHERE NOT cancelado
            UNION
            SELECT chave, data_entrega_simulada FROM pedidos WHERE NOT cancelado
        )
        SELECT chave, dia AS data_lote, false AS foto
        FROM eventos WHERE dia > DATE '{data_corte}' AND dia <= DATE '{horizonte}';
    """)


def consultas_movimento(estado):
    """Monta as consultas de cada arquivo, com a situação do pedido na data do lote."""
    return {
        "pedidos": f"""
            SELECT e.data_lote, p.codigo, p.codigo_cliente, p.codigo_cd, p.data_pedido,
                   status_em(p.cancelado, p.data_envio, p.data_entrega_simulada, e.data_lote) AS status,
                   p.tipo_frete, p.valor_produtos, p.valor_desconto, p.valor_frete,
                   p.valor_produtos - p.valor_desconto + p.valor_frete AS valor_total
            FROM {estado} e JOIN pedidos p USING (chave)
        """,
        # Itens e notas não mudam: entram só no lote em que surgem.
        "itens_pedido": f"""
            SELECT e.data_lote, p.codigo AS codigo_pedido, i.numero_item, i.codigo_produto, i.quantidade,
                   i.preco_unitario, i.desconto_pct, i.valor_bruto, i.valor_desconto,
                   i.valor_bruto - i.valor_desconto AS valor_liquido, i.peso_kg, i.volume_m3
            FROM {estado} e
            JOIN pedidos p USING (chave)
            JOIN itens i ON i.chave_pedido = p.chave
            WHERE e.foto OR e.data_lote = p.data_pedido
        """,
        "notas_fiscais": f"""
            SELECT e.data_lote, n.chave_nfe, n.numero, '001' AS serie, n.data_envio AS data_emissao,
                   n.codigo AS codigo_pedido, n.cnpj_emitente, n.cnpj_cliente AS cnpj_destinatario,
                   CASE WHEN n.uf_origem = n.uf_destino THEN '5102' ELSE '6102' END AS cfop,
                   n.aliquota_icms,
                   round((n.valor_produtos - n.valor_desconto) * n.aliquota_icms / 100, 2)::DECIMAL(14, 2) AS valor_icms,
                   n.valor_produtos, n.valor_desconto,
                   CASE WHEN n.tipo_frete = 'CIF' THEN n.valor_frete ELSE 0 END AS valor_frete,
                   n.valor_produtos - n.valor_desconto
                   + CASE WHEN n.tipo_frete = 'CIF' THEN n.valor_frete ELSE 0 END AS valor_total
            FROM {estado} e JOIN notas n USING (chave)
            WHERE n.data_envio <= e.data_lote AND (e.foto OR n.data_envio = e.data_lote)
        """,
        "entregas": f"""
            SELECT e.data_lote, 'ENT-' || lpad(n.chave::VARCHAR, 9, '0') AS codigo, n.codigo AS codigo_pedido,
                   n.chave_nfe, n.codigo_transportadora, d.codigo_local AS local_origem, n.local_destino, n.modal,
                   round(n.distancia_km, 1) AS distancia_km, n.data_envio, n.data_previsao,
                   CASE WHEN n.data_entrega_simulada <= e.data_lote THEN n.data_entrega_simulada END AS data_entrega,
                   n.peso_kg, n.volume_m3, n.valor_frete,
                   CASE
                       WHEN n.data_entrega_simulada > e.data_lote THEN 'Em trânsito'
                       WHEN n.atrasou THEN escolher({lista_sql(OCORRENCIAS)}, 'ocorrencia', n.chave)
                       ELSE 'Sem ocorrência'
                   END AS ocorrencia
            FROM {estado} e
            JOIN notas n USING (chave)
            JOIN centros d ON d.codigo = n.codigo_cd
            WHERE n.data_envio <= e.data_lote
        """,
    }


def exportar_simulado(con, saida):
    pasta = saida / "simulado"
    exportar(con, "SELECT codigo, cidade, uf, regiao, pais, lat AS latitude, lon AS longitude FROM locais ORDER BY codigo",
             pasta / "locais.csv")
    exportar(con, "SELECT codigo, nome, cnpj, codigo_local FROM centros ORDER BY codigo",
             pasta / "centros_distribuicao.csv")
    exportar(con, "SELECT codigo, nome, cnpj, modal FROM transportadoras ORDER BY codigo",
             pasta / "transportadoras.csv")
    exportar(con, """
        SELECT codigo, prefixo || ' ' || sobrenomes || ' Ltda' AS razao_social, cnpj, logradouro, numero,
               cidade, uf, cep, codigo_local
        FROM clientes ORDER BY codigo
    """, pasta / "clientes.csv")
    exportar(con, """
        SELECT codigo, descricao, categoria, marca, preco_unitario, peso_kg, volume_m3 FROM produtos ORDER BY codigo
    """, pasta / "produtos.csv")
    ordens = {
        "pedidos": "codigo",
        "itens_pedido": "codigo_pedido, numero_item",
        "notas_fiscais": "codigo_pedido",
        "entregas": "codigo",
    }
    for nome, consulta in consultas_movimento("estado_foto").items():
        exportar(con, f"SELECT * EXCLUDE (data_lote) FROM ({consulta}) ORDER BY {ordens[nome]}",
                 pasta / f"{nome}.csv")


def exportar_lotes_diarios(con, saida):
    pasta = saida / "lotes"
    shutil.rmtree(pasta, ignore_errors=True)
    for nome, consulta in consultas_movimento("estado_lotes").items():
        exportar_lotes(con, consulta, pasta / nome)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--escala", type=float, default=1, help="fator de escala do TPC-H (1 = 1,5 milhão de pedidos)")
    parser.add_argument("--saida", type=Path, default=Path("data"), help="pasta de destino dos CSVs")
    parser.add_argument("--data-corte", type=date.fromisoformat, default=date(2026, 11, 1),
                        help="data que a foto da operação trata como hoje")
    parser.add_argument("--dias-lote", type=int, default=365, help="dias de lotes diários depois da data de corte")
    args = parser.parse_args()
    horizonte = args.data_corte + timedelta(days=args.dias_lote)

    args.saida.mkdir(parents=True, exist_ok=True)
    arquivo_temp = args.saida / ".geracao.duckdb"
    arquivo_temp.unlink(missing_ok=True)
    con = duckdb.connect(str(arquivo_temp))
    try:
        con.execute("INSTALL tpch; LOAD tpch;")
        con.execute(f"CALL dbgen(sf={args.escala})")
        exportar_tpch(con, args.saida)
        criar_referencias(con)
        criar_cadastros(con)
        criar_movimento(con, horizonte)
        criar_estados(con, args.data_corte, horizonte)
        exportar_simulado(con, args.saida)
        exportar_lotes_diarios(con, args.saida)
        (args.saida / "manifesto.json").write_text(
            json.dumps({"data_corte": args.data_corte.isoformat(), "dias_lote": args.dias_lote}), encoding="utf-8"
        )
    finally:
        con.close()
        arquivo_temp.unlink(missing_ok=True)
        Path(f"{arquivo_temp}.wal").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
