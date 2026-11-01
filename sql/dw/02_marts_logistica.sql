-- Modelo estrela inicial de logística. Revisar quando a fonte de dados for definida.
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

CREATE TABLE IF NOT EXISTS marts.dim_carrier (
    carrier_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    carrier_code  text NOT NULL UNIQUE,
    carrier_name  text NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.dim_location (
    location_key   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_code  text NOT NULL UNIQUE,
    city           text NOT NULL,
    state          text NOT NULL,
    country        text NOT NULL DEFAULT 'BR'
);

CREATE TABLE IF NOT EXISTS marts.fact_shipment (
    shipment_key              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    shipment_code             text           NOT NULL UNIQUE,
    carrier_key               bigint         NOT NULL REFERENCES marts.dim_carrier,
    origin_location_key       bigint         NOT NULL REFERENCES marts.dim_location,
    destination_location_key  bigint         NOT NULL REFERENCES marts.dim_location,
    shipped_date_key          integer        NOT NULL REFERENCES marts.dim_date,
    promised_date_key         integer        REFERENCES marts.dim_date,
    delivered_date_key        integer        REFERENCES marts.dim_date,
    weight_kg                 numeric(12, 3),
    freight_cost              numeric(14, 2),
    load_run_id               bigint         REFERENCES audit.load_run
);
