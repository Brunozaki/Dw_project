-- Modelo estrela de logística, alimentado pelos arquivos de scripts/gerar_dados_logistica.py.
CREATE TABLE IF NOT EXISTS marts.dim_date (
    date_key     integer  PRIMARY KEY,
    full_date    date     NOT NULL UNIQUE,
    year         smallint NOT NULL,
    quarter      smallint NOT NULL,
    month        smallint NOT NULL,
    day          smallint NOT NULL,
    day_of_week  smallint NOT NULL,
    is_weekend   boolean  NOT NULL
);

INSERT INTO marts.dim_date
SELECT
    to_char(d, 'YYYYMMDD')::integer,
    d::date,
    extract(year FROM d)::smallint,
    extract(quarter FROM d)::smallint,
    extract(month FROM d)::smallint,
    extract(day FROM d)::smallint,
    extract(isodow FROM d)::smallint,
    extract(isodow FROM d) IN (6, 7)
FROM generate_series('2020-01-01'::date, '2035-12-31'::date, interval '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS marts.dim_location (
    location_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_code  text NOT NULL UNIQUE,
    city           text NOT NULL,
    state          text NOT NULL,
    region         text NOT NULL,
    country        text NOT NULL DEFAULT 'BR',
    latitude       numeric(8, 5),
    longitude      numeric(8, 5)
);

CREATE TABLE IF NOT EXISTS marts.dim_carrier (
    carrier_key     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    carrier_code    text NOT NULL UNIQUE,
    carrier_name    text NOT NULL,
    transport_mode  text NOT NULL,
    tax_id          text NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.dim_distribution_center (
    distribution_center_key  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    distribution_center_code text   NOT NULL UNIQUE,
    distribution_center_name text   NOT NULL,
    tax_id                   text   NOT NULL,
    location_key             bigint NOT NULL REFERENCES marts.dim_location
);

CREATE TABLE IF NOT EXISTS marts.dim_customer (
    customer_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_code  text   NOT NULL UNIQUE,
    legal_name     text   NOT NULL,
    tax_id         text   NOT NULL,
    zip_code       text   NOT NULL,
    location_key   bigint NOT NULL REFERENCES marts.dim_location
);

CREATE TABLE IF NOT EXISTS marts.dim_product (
    product_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_code  text           NOT NULL UNIQUE,
    description   text           NOT NULL,
    category      text           NOT NULL,
    brand         text           NOT NULL,
    unit_price    numeric(12, 2) NOT NULL,
    weight_kg     numeric(10, 3) NOT NULL,
    volume_m3     numeric(10, 4) NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.fact_order (
    order_key                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_code               text           NOT NULL UNIQUE,
    customer_key             bigint         NOT NULL REFERENCES marts.dim_customer,
    distribution_center_key  bigint         NOT NULL REFERENCES marts.dim_distribution_center,
    order_date_key           integer        NOT NULL REFERENCES marts.dim_date,
    status                   text           NOT NULL,
    freight_type             text           NOT NULL,
    product_amount           numeric(14, 2) NOT NULL,
    discount_amount          numeric(14, 2) NOT NULL,
    freight_amount           numeric(14, 2) NOT NULL,
    total_amount             numeric(14, 2) NOT NULL,
    load_run_id              bigint         REFERENCES audit.load_run
);

CREATE TABLE IF NOT EXISTS marts.fact_order_item (
    order_key        bigint         NOT NULL REFERENCES marts.fact_order,
    item_number      integer        NOT NULL,
    product_key      bigint         NOT NULL REFERENCES marts.dim_product,
    quantity         integer        NOT NULL,
    unit_price       numeric(12, 2) NOT NULL,
    discount_pct     numeric(4, 2)  NOT NULL,
    gross_amount     numeric(14, 2) NOT NULL,
    discount_amount  numeric(14, 2) NOT NULL,
    net_amount       numeric(14, 2) NOT NULL,
    weight_kg        numeric(12, 3) NOT NULL,
    volume_m3        numeric(12, 4) NOT NULL,
    load_run_id      bigint         REFERENCES audit.load_run,
    PRIMARY KEY (order_key, item_number)
);

CREATE TABLE IF NOT EXISTS marts.fact_invoice (
    invoice_key      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    access_key       text           NOT NULL UNIQUE,
    invoice_number   bigint         NOT NULL,
    series           text           NOT NULL,
    order_key        bigint         NOT NULL REFERENCES marts.fact_order,
    issue_date_key   integer        NOT NULL REFERENCES marts.dim_date,
    cfop             text           NOT NULL,
    icms_rate        numeric(5, 2)  NOT NULL,
    icms_amount      numeric(14, 2) NOT NULL,
    product_amount   numeric(14, 2) NOT NULL,
    discount_amount  numeric(14, 2) NOT NULL,
    freight_amount   numeric(14, 2) NOT NULL,
    total_amount     numeric(14, 2) NOT NULL,
    load_run_id      bigint         REFERENCES audit.load_run
);

CREATE TABLE IF NOT EXISTS marts.fact_shipment (
    shipment_key              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_code             text           NOT NULL UNIQUE,
    order_key                 bigint         NOT NULL REFERENCES marts.fact_order,
    invoice_key               bigint         NOT NULL REFERENCES marts.fact_invoice,
    carrier_key               bigint         NOT NULL REFERENCES marts.dim_carrier,
    origin_location_key       bigint         NOT NULL REFERENCES marts.dim_location,
    destination_location_key  bigint         NOT NULL REFERENCES marts.dim_location,
    shipped_date_key          integer        NOT NULL REFERENCES marts.dim_date,
    promised_date_key         integer        REFERENCES marts.dim_date,
    delivered_date_key        integer        REFERENCES marts.dim_date,
    transport_mode            text           NOT NULL,
    distance_km               numeric(10, 1),
    weight_kg                 numeric(12, 3),
    volume_m3                 numeric(12, 4),
    freight_cost              numeric(14, 2),
    occurrence                text           NOT NULL,
    -- Fica vazio até a entrega acontecer.
    is_late                   boolean GENERATED ALWAYS AS (delivered_date_key > promised_date_key) STORED,
    load_run_id               bigint         REFERENCES audit.load_run
);

CREATE INDEX IF NOT EXISTS fact_order_order_date_idx ON marts.fact_order (order_date_key);
CREATE INDEX IF NOT EXISTS fact_shipment_shipped_date_idx ON marts.fact_shipment (shipped_date_key);
CREATE INDEX IF NOT EXISTS fact_shipment_carrier_idx ON marts.fact_shipment (carrier_key);
