"""Carrega a foto inicial e os lotes diários nas camadas raw e marts.

Cada lote roda em uma transação: se algo falhar, nada dele fica no banco, e a próxima
execução recomeça desse lote. Sem imports do Airflow, para os testes rodarem sem ele.
"""
import json
from datetime import date
from pathlib import Path

PASTA_SQL = Path(__file__).parent / "sql"
TABELAS_CADASTRO = ("locais", "centros_distribuicao", "transportadoras", "clientes", "produtos")
TABELAS_MOVIMENTO = ("pedidos", "itens_pedido", "notas_fiscais", "entregas")
TAMANHO_BLOCO = 1024 * 1024

# Cada consulta conta as linhas do lote que quebram a regra. Rodam depois das dimensões
# e antes dos fatos, porque os JOINs dos fatos descartariam essas linhas em silêncio.
VALIDACOES = {
    "pedido duplicado no lote": """
        SELECT count(*) - count(DISTINCT codigo) FROM staging.pedidos WHERE lote = %(lote)s
    """,
    "entrega duplicada no lote": """
        SELECT count(*) - count(DISTINCT codigo) FROM staging.entregas WHERE lote = %(lote)s
    """,
    "pedido com status desconhecido": """
        SELECT count(*) FROM staging.pedidos WHERE lote = %(lote)s
          AND status NOT IN ('aguardando_envio', 'em_transito', 'entregue', 'cancelado')
    """,
    "pedido com valor negativo": """
        SELECT count(*) FROM staging.pedidos WHERE lote = %(lote)s
          AND least(valor_produtos, valor_desconto, valor_frete, valor_total) < 0
    """,
    "pedido sem cliente ou centro de distribuição": """
        SELECT count(*) FROM staging.pedidos p
        LEFT JOIN marts.dim_customer c ON c.customer_code = p.codigo_cliente
        LEFT JOIN marts.dim_distribution_center d ON d.distribution_center_code = p.codigo_cd
        WHERE p.lote = %(lote)s AND (c.customer_key IS NULL OR d.distribution_center_key IS NULL)
    """,
    "item sem pedido no lote": """
        SELECT count(*) FROM staging.itens_pedido i
        LEFT JOIN staging.pedidos p ON p.lote = i.lote AND p.codigo = i.codigo_pedido
        WHERE i.lote = %(lote)s AND p.codigo IS NULL
    """,
    "item sem produto": """
        SELECT count(*) FROM staging.itens_pedido i
        LEFT JOIN marts.dim_product p ON p.product_code = i.codigo_produto
        WHERE i.lote = %(lote)s AND p.product_key IS NULL
    """,
    "nota sem pedido no lote": """
        SELECT count(*) FROM staging.notas_fiscais n
        LEFT JOIN staging.pedidos p ON p.lote = n.lote AND p.codigo = n.codigo_pedido
        WHERE n.lote = %(lote)s AND p.codigo IS NULL
    """,
    "entrega sem pedido no lote": """
        SELECT count(*) FROM staging.entregas e
        LEFT JOIN staging.pedidos p ON p.lote = e.lote AND p.codigo = e.codigo_pedido
        WHERE e.lote = %(lote)s AND p.codigo IS NULL
    """,
    "entrega sem transportadora ou local": """
        SELECT count(*) FROM staging.entregas e
        LEFT JOIN marts.dim_carrier c ON c.carrier_code = e.codigo_transportadora
        LEFT JOIN marts.dim_location lo ON lo.location_code = e.local_origem
        LEFT JOIN marts.dim_location ld ON ld.location_code = e.local_destino
        WHERE e.lote = %(lote)s
          AND (c.carrier_key IS NULL OR lo.location_key IS NULL OR ld.location_key IS NULL)
    """,
    "entrega sem nota fiscal": """
        SELECT count(*) FROM staging.entregas e
        LEFT JOIN staging.notas_fiscais n ON n.lote = e.lote AND n.chave_nfe = e.chave_nfe
        LEFT JOIN marts.fact_invoice f ON f.access_key = e.chave_nfe
        WHERE e.lote = %(lote)s AND n.chave_nfe IS NULL AND f.invoice_key IS NULL
    """,
    "entrega antes do envio": """
        SELECT count(*) FROM staging.entregas WHERE lote = %(lote)s AND data_entrega < data_envio
    """,
}


def ler_data_corte(pasta_dados):
    arquivo = Path(pasta_dados) / "manifesto.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"{arquivo} não existe. Rode scripts/gerar_dados_logistica.py")
    return date.fromisoformat(json.loads(arquivo.read_text(encoding="utf-8"))["data_corte"])


def listar_lotes(pasta_dados):
    pasta = Path(pasta_dados) / "lotes" / "pedidos"
    return sorted(date.fromisoformat(p.name.split("=")[1]) for p in pasta.glob("data_lote=*"))


def lotes_pendentes(data_corte, disponiveis, ultimo_carregado, hoje):
    """Só entram dias já encerrados. Dias perdidos entram todos, em ordem."""
    if ultimo_carregado is None:
        return [data_corte] + [d for d in disponiveis if data_corte < d < hoje]
    return [d for d in disponiveis if ultimo_carregado < d < hoje]


def arquivos_do_lote(pasta_dados, data_corte, lote):
    """Retorna {tabela: [arquivos]}. A foto inicial traz também os cadastros."""
    pasta = Path(pasta_dados)
    if lote == data_corte:
        tabelas = TABELAS_CADASTRO + TABELAS_MOVIMENTO
        return {t: [pasta / "simulado" / f"{t}.csv"] for t in tabelas}
    return {t: sorted((pasta / "lotes" / t / f"data_lote={lote}").glob("*.csv")) for t in TABELAS_MOVIMENTO}


def enviar_copy(cur, comando, arquivo):
    """A imagem Docker do Airflow usa psycopg3, e a instalação manual pode usar psycopg2."""
    if hasattr(cur, "copy_expert"):
        cur.copy_expert(comando, arquivo)
        return
    with cur.copy(comando) as copia:
        while bloco := arquivo.read(TAMANHO_BLOCO):
            copia.write(bloco)


def copiar_para_raw(cur, tabela, arquivos, lote):
    cur.execute(f"DELETE FROM raw.{tabela} WHERE lote = %s", (lote,))
    linhas = 0
    for arquivo in arquivos:
        with open(arquivo, "rb") as f:
            colunas = f.readline().decode("utf-8").strip()
            enviar_copy(cur, f"COPY raw.{tabela} ({colunas}) FROM STDIN WITH (FORMAT csv)", f)
        linhas += cur.rowcount
    return linhas


def validar(cur, lote):
    problemas = {}
    for nome, consulta in VALIDACOES.items():
        cur.execute(consulta, {"lote": lote})
        quantidade = cur.fetchone()[0]
        if quantidade:
            problemas[nome] = quantidade
    if problemas:
        raise ValueError(f"Lote {lote} reprovado na validação: {problemas}")


def dividir_comandos(texto):
    """O psycopg3 não aceita vários comandos com parâmetros em uma só chamada."""
    return [comando.strip() for comando in texto.split(";\n") if comando.strip()]


def executar_sql(cur, arquivo, parametros):
    for comando in dividir_comandos((PASTA_SQL / arquivo).read_text(encoding="utf-8")):
        cur.execute(comando, parametros)


def carregar_lote(conn, pasta_dados, data_corte, lote, load_run_id):
    parametros = {"lote": lote, "load_run_id": load_run_id}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('dw.lote', %s, true)", (lote.isoformat(),))
            linhas = 0
            for tabela, arquivos in arquivos_do_lote(pasta_dados, data_corte, lote).items():
                linhas += copiar_para_raw(cur, tabela, arquivos, lote)
            if linhas == 0:
                raise ValueError(f"Lote {lote} sem linhas")
            executar_sql(cur, "01_dimensoes.sql", parametros)
            validar(cur, lote)
            executar_sql(cur, "02_fatos.sql", parametros)
            cur.execute(
                """
                INSERT INTO audit.loaded_batch (batch_date, load_run_id, rows_loaded)
                VALUES (%s, %s, %s)
                ON CONFLICT (batch_date) DO UPDATE SET
                    load_run_id = EXCLUDED.load_run_id, rows_loaded = EXCLUDED.rows_loaded, loaded_at = now()
                """,
                (lote, load_run_id, linhas),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return linhas
