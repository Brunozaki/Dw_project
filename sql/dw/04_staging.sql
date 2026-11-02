-- Visões com os dados do raw limpos e nos tipos corretos.
CREATE OR REPLACE VIEW staging.locais AS
SELECT lote, trim(codigo) AS codigo, trim(cidade) AS cidade, upper(trim(uf)) AS uf, trim(regiao) AS regiao,
       upper(trim(pais)) AS pais, latitude::numeric(8, 5) AS latitude, longitude::numeric(8, 5) AS longitude
FROM raw.locais;

CREATE OR REPLACE VIEW staging.centros_distribuicao AS
SELECT lote, trim(codigo) AS codigo, trim(nome) AS nome, trim(cnpj) AS cnpj, trim(codigo_local) AS codigo_local
FROM raw.centros_distribuicao;

CREATE OR REPLACE VIEW staging.transportadoras AS
SELECT lote, trim(codigo) AS codigo, trim(nome) AS nome, trim(cnpj) AS cnpj, trim(modal) AS modal
FROM raw.transportadoras;

CREATE OR REPLACE VIEW staging.clientes AS
SELECT lote, trim(codigo) AS codigo, trim(razao_social) AS razao_social, trim(cnpj) AS cnpj,
       trim(cep) AS cep, trim(codigo_local) AS codigo_local
FROM raw.clientes;

CREATE OR REPLACE VIEW staging.produtos AS
SELECT lote, trim(codigo) AS codigo, trim(descricao) AS descricao, trim(categoria) AS categoria, trim(marca) AS marca,
       preco_unitario::numeric(12, 2) AS preco_unitario, peso_kg::numeric(10, 3) AS peso_kg,
       volume_m3::numeric(10, 4) AS volume_m3
FROM raw.produtos;

CREATE OR REPLACE VIEW staging.pedidos AS
SELECT lote, trim(codigo) AS codigo, trim(codigo_cliente) AS codigo_cliente, trim(codigo_cd) AS codigo_cd,
       data_pedido::date AS data_pedido, lower(trim(status)) AS status, upper(trim(tipo_frete)) AS tipo_frete,
       valor_produtos::numeric(14, 2) AS valor_produtos, valor_desconto::numeric(14, 2) AS valor_desconto,
       valor_frete::numeric(14, 2) AS valor_frete, valor_total::numeric(14, 2) AS valor_total
FROM raw.pedidos;

CREATE OR REPLACE VIEW staging.itens_pedido AS
SELECT lote, trim(codigo_pedido) AS codigo_pedido, numero_item::integer AS numero_item,
       trim(codigo_produto) AS codigo_produto, quantidade::integer AS quantidade,
       preco_unitario::numeric(12, 2) AS preco_unitario, desconto_pct::numeric(4, 2) AS desconto_pct,
       valor_bruto::numeric(14, 2) AS valor_bruto, valor_desconto::numeric(14, 2) AS valor_desconto,
       valor_liquido::numeric(14, 2) AS valor_liquido, peso_kg::numeric(12, 3) AS peso_kg,
       volume_m3::numeric(12, 4) AS volume_m3
FROM raw.itens_pedido;

CREATE OR REPLACE VIEW staging.notas_fiscais AS
SELECT lote, trim(chave_nfe) AS chave_nfe, numero::bigint AS numero, trim(serie) AS serie,
       data_emissao::date AS data_emissao, trim(codigo_pedido) AS codigo_pedido, trim(cfop) AS cfop,
       aliquota_icms::numeric(5, 2) AS aliquota_icms, valor_icms::numeric(14, 2) AS valor_icms,
       valor_produtos::numeric(14, 2) AS valor_produtos, valor_desconto::numeric(14, 2) AS valor_desconto,
       valor_frete::numeric(14, 2) AS valor_frete, valor_total::numeric(14, 2) AS valor_total
FROM raw.notas_fiscais;

CREATE OR REPLACE VIEW staging.entregas AS
SELECT lote, trim(codigo) AS codigo, trim(codigo_pedido) AS codigo_pedido, trim(chave_nfe) AS chave_nfe,
       trim(codigo_transportadora) AS codigo_transportadora, trim(local_origem) AS local_origem,
       trim(local_destino) AS local_destino, trim(modal) AS modal, distancia_km::numeric(10, 1) AS distancia_km,
       data_envio::date AS data_envio, data_previsao::date AS data_previsao, data_entrega::date AS data_entrega,
       peso_kg::numeric(12, 3) AS peso_kg, volume_m3::numeric(12, 4) AS volume_m3,
       valor_frete::numeric(14, 2) AS valor_frete, trim(ocorrencia) AS ocorrencia
FROM raw.entregas;
