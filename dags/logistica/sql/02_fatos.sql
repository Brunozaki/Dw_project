-- Fatos do lote. Um pedido ou entrega que já existe é atualizado, não duplicado.
INSERT INTO marts.fact_order (
    order_code, customer_key, distribution_center_key, order_date_key, status, freight_type,
    product_amount, discount_amount, freight_amount, total_amount, load_run_id
)
SELECT p.codigo, c.customer_key, d.distribution_center_key, to_char(p.data_pedido, 'YYYYMMDD')::integer,
       p.status, p.tipo_frete, p.valor_produtos, p.valor_desconto, p.valor_frete, p.valor_total, %(load_run_id)s
FROM staging.pedidos p
JOIN marts.dim_customer c ON c.customer_code = p.codigo_cliente
JOIN marts.dim_distribution_center d ON d.distribution_center_code = p.codigo_cd
WHERE p.lote = %(lote)s
ON CONFLICT (order_code) DO UPDATE SET
    status = EXCLUDED.status, load_run_id = EXCLUDED.load_run_id;

INSERT INTO marts.fact_order_item (
    order_key, item_number, product_key, quantity, unit_price, discount_pct,
    gross_amount, discount_amount, net_amount, weight_kg, volume_m3, load_run_id
)
SELECT o.order_key, i.numero_item, p.product_key, i.quantidade, i.preco_unitario, i.desconto_pct,
       i.valor_bruto, i.valor_desconto, i.valor_liquido, i.peso_kg, i.volume_m3, %(load_run_id)s
FROM staging.itens_pedido i
JOIN marts.fact_order o ON o.order_code = i.codigo_pedido
JOIN marts.dim_product p ON p.product_code = i.codigo_produto
WHERE i.lote = %(lote)s
ON CONFLICT (order_key, item_number) DO NOTHING;

INSERT INTO marts.fact_invoice (
    access_key, invoice_number, series, order_key, issue_date_key, cfop, icms_rate, icms_amount,
    product_amount, discount_amount, freight_amount, total_amount, load_run_id
)
SELECT n.chave_nfe, n.numero, n.serie, o.order_key, to_char(n.data_emissao, 'YYYYMMDD')::integer, n.cfop,
       n.aliquota_icms, n.valor_icms, n.valor_produtos, n.valor_desconto, n.valor_frete, n.valor_total, %(load_run_id)s
FROM staging.notas_fiscais n
JOIN marts.fact_order o ON o.order_code = n.codigo_pedido
WHERE n.lote = %(lote)s
ON CONFLICT (access_key) DO NOTHING;

INSERT INTO marts.fact_shipment (
    shipment_code, order_key, invoice_key, carrier_key, origin_location_key, destination_location_key,
    shipped_date_key, promised_date_key, delivered_date_key, transport_mode, distance_km,
    weight_kg, volume_m3, freight_cost, occurrence, load_run_id
)
SELECT e.codigo, o.order_key, n.invoice_key, c.carrier_key, lo.location_key, ld.location_key,
       to_char(e.data_envio, 'YYYYMMDD')::integer, to_char(e.data_previsao, 'YYYYMMDD')::integer,
       to_char(e.data_entrega, 'YYYYMMDD')::integer, e.modal, e.distancia_km,
       e.peso_kg, e.volume_m3, e.valor_frete, e.ocorrencia, %(load_run_id)s
FROM staging.entregas e
JOIN marts.fact_order o ON o.order_code = e.codigo_pedido
JOIN marts.fact_invoice n ON n.access_key = e.chave_nfe
JOIN marts.dim_carrier c ON c.carrier_code = e.codigo_transportadora
JOIN marts.dim_location lo ON lo.location_code = e.local_origem
JOIN marts.dim_location ld ON ld.location_code = e.local_destino
WHERE e.lote = %(lote)s
ON CONFLICT (shipment_code) DO UPDATE SET
    delivered_date_key = EXCLUDED.delivered_date_key, occurrence = EXCLUDED.occurrence,
    load_run_id = EXCLUDED.load_run_id;
