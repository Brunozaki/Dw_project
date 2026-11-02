-- Tabelas de chegada: tudo em texto, sem regras, para aceitar o arquivo como veio.
-- A coluna lote guarda a data do lote. A carga define o valor na configuração dw.lote,
-- porque o COPY só preenche as colunas presentes no arquivo.
CREATE TABLE IF NOT EXISTS raw.locais (
    codigo text, cidade text, uf text, regiao text, pais text, latitude text, longitude text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.centros_distribuicao (
    codigo text, nome text, cnpj text, codigo_local text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.transportadoras (
    codigo text, nome text, cnpj text, modal text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.clientes (
    codigo text, razao_social text, cnpj text, logradouro text, numero text,
    cidade text, uf text, cep text, codigo_local text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.produtos (
    codigo text, descricao text, categoria text, marca text,
    preco_unitario text, peso_kg text, volume_m3 text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.pedidos (
    codigo text, codigo_cliente text, codigo_cd text, data_pedido text, status text, tipo_frete text,
    valor_produtos text, valor_desconto text, valor_frete text, valor_total text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.itens_pedido (
    codigo_pedido text, numero_item text, codigo_produto text, quantidade text, preco_unitario text,
    desconto_pct text, valor_bruto text, valor_desconto text, valor_liquido text, peso_kg text, volume_m3 text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.notas_fiscais (
    chave_nfe text, numero text, serie text, data_emissao text, codigo_pedido text,
    cnpj_emitente text, cnpj_destinatario text, cfop text, aliquota_icms text, valor_icms text,
    valor_produtos text, valor_desconto text, valor_frete text, valor_total text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.entregas (
    codigo text, codigo_pedido text, chave_nfe text, codigo_transportadora text,
    local_origem text, local_destino text, modal text, distancia_km text,
    data_envio text, data_previsao text, data_entrega text,
    peso_kg text, volume_m3 text, valor_frete text, ocorrencia text,
    lote date NOT NULL DEFAULT current_setting('dw.lote')::date,
    carregado_em timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS locais_lote_idx ON raw.locais (lote);
CREATE INDEX IF NOT EXISTS centros_distribuicao_lote_idx ON raw.centros_distribuicao (lote);
CREATE INDEX IF NOT EXISTS transportadoras_lote_idx ON raw.transportadoras (lote);
CREATE INDEX IF NOT EXISTS clientes_lote_idx ON raw.clientes (lote);
CREATE INDEX IF NOT EXISTS produtos_lote_idx ON raw.produtos (lote);
CREATE INDEX IF NOT EXISTS pedidos_lote_idx ON raw.pedidos (lote);
CREATE INDEX IF NOT EXISTS itens_pedido_lote_idx ON raw.itens_pedido (lote);
CREATE INDEX IF NOT EXISTS notas_fiscais_lote_idx ON raw.notas_fiscais (lote);
CREATE INDEX IF NOT EXISTS entregas_lote_idx ON raw.entregas (lote);
