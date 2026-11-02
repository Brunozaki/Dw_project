import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "dags"))

from logistica.carga import (
    PASTA_SQL,
    arquivos_do_lote,
    dividir_comandos,
    ler_data_corte,
    listar_lotes,
    lotes_pendentes,
)

CORTE = date(2026, 11, 1)
DIA_2 = date(2026, 11, 2)
DIA_3 = date(2026, 11, 3)
DIA_4 = date(2026, 11, 4)
LOTES = [DIA_2, DIA_3, DIA_4]


def test_primeira_carga_comeca_pela_foto():
    assert lotes_pendentes(CORTE, LOTES, None, DIA_3) == [CORTE, DIA_2]


def test_dia_atual_fica_de_fora():
    assert lotes_pendentes(CORTE, LOTES, CORTE, DIA_2) == []


def test_dias_perdidos_entram_em_ordem():
    assert lotes_pendentes(CORTE, LOTES, CORTE, date(2026, 11, 10)) == LOTES


def test_lote_carregado_nao_repete():
    assert lotes_pendentes(CORTE, LOTES, DIA_3, date(2026, 11, 10)) == [DIA_4]


def test_listar_lotes_ordena_pastas(tmp_path):
    for dia in ("2026-11-03", "2026-11-02"):
        (tmp_path / "lotes" / "pedidos" / f"data_lote={dia}").mkdir(parents=True)
    assert listar_lotes(tmp_path) == [DIA_2, DIA_3]


def test_foto_traz_cadastros_e_lote_nao(tmp_path):
    foto = arquivos_do_lote(tmp_path, CORTE, CORTE)
    lote = arquivos_do_lote(tmp_path, CORTE, DIA_2)
    assert "clientes" in foto and "pedidos" in foto
    assert "clientes" not in lote and "pedidos" in lote


def test_dividir_comandos_separa_um_por_vez():
    assert dividir_comandos("-- nota\nSELECT 1;\n\nSELECT 2;\n") == ["-- nota\nSELECT 1", "SELECT 2"]


def test_sql_da_carga_tem_um_insert_por_comando():
    for arquivo in PASTA_SQL.glob("*.sql"):
        for comando in dividir_comandos(arquivo.read_text(encoding="utf-8")):
            assert comando.count("INSERT INTO") == 1


def test_ler_data_corte(tmp_path):
    (tmp_path / "manifesto.json").write_text(json.dumps({"data_corte": "2026-11-01"}), encoding="utf-8")
    assert ler_data_corte(tmp_path) == CORTE
