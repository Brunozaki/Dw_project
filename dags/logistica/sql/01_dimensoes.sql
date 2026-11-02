-- Cadastros do lote. Os lotes diários não trazem cadastros, então aqui nada muda neles.
INSERT INTO marts.dim_location (location_code, city, state, region, country, latitude, longitude)
SELECT codigo, cidade, uf, regiao, pais, latitude, longitude
FROM staging.locais
WHERE lote = %(lote)s
ON CONFLICT (location_code) DO UPDATE SET
    city = EXCLUDED.city, state = EXCLUDED.state, region = EXCLUDED.region, country = EXCLUDED.country,
    latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude;

INSERT INTO marts.dim_carrier (carrier_code, carrier_name, transport_mode, tax_id)
SELECT codigo, nome, modal, cnpj
FROM staging.transportadoras
WHERE lote = %(lote)s
ON CONFLICT (carrier_code) DO UPDATE SET
    carrier_name = EXCLUDED.carrier_name, transport_mode = EXCLUDED.transport_mode, tax_id = EXCLUDED.tax_id;

INSERT INTO marts.dim_distribution_center (distribution_center_code, distribution_center_name, tax_id, location_key)
SELECT c.codigo, c.nome, c.cnpj, l.location_key
FROM staging.centros_distribuicao c
JOIN marts.dim_location l ON l.location_code = c.codigo_local
WHERE c.lote = %(lote)s
ON CONFLICT (distribution_center_code) DO UPDATE SET
    distribution_center_name = EXCLUDED.distribution_center_name, tax_id = EXCLUDED.tax_id,
    location_key = EXCLUDED.location_key;

INSERT INTO marts.dim_customer (customer_code, legal_name, tax_id, zip_code, location_key)
SELECT c.codigo, c.razao_social, c.cnpj, c.cep, l.location_key
FROM staging.clientes c
JOIN marts.dim_location l ON l.location_code = c.codigo_local
WHERE c.lote = %(lote)s
ON CONFLICT (customer_code) DO UPDATE SET
    legal_name = EXCLUDED.legal_name, tax_id = EXCLUDED.tax_id, zip_code = EXCLUDED.zip_code,
    location_key = EXCLUDED.location_key;

INSERT INTO marts.dim_product (product_code, description, category, brand, unit_price, weight_kg, volume_m3)
SELECT codigo, descricao, categoria, marca, preco_unitario, peso_kg, volume_m3
FROM staging.produtos
WHERE lote = %(lote)s
ON CONFLICT (product_code) DO UPDATE SET
    description = EXCLUDED.description, category = EXCLUDED.category, brand = EXCLUDED.brand,
    unit_price = EXCLUDED.unit_price, weight_kg = EXCLUDED.weight_kg, volume_m3 = EXCLUDED.volume_m3;
