-- DDL para a camada bronze
-- Convenção: schema = camada, tabela = dominio__entidade
-- Colunas _extracted_at e _source preenchidas pelo script de carga (SPEC 03)

-- ===========================
-- SCHEMAS
-- ===========================
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ===========================
-- TABELAS BRONZE
-- ===========================

CREATE TABLE IF NOT EXISTS bronze.olist__orders (
    order_id                      TEXT        NOT NULL,
    customer_id                   TEXT        NOT NULL,
    order_status                  TEXT        NOT NULL,
    order_purchase_timestamp      TIMESTAMPTZ NOT NULL,
    order_approved_at             TIMESTAMPTZ,
    order_delivered_carrier_date  TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ NOT NULL,
    _extracted_at                 TIMESTAMPTZ NOT NULL,
    _source                       TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.olist__order_items (
    order_id            TEXT          NOT NULL,
    order_item_id       INTEGER       NOT NULL,
    product_id          TEXT          NOT NULL,
    seller_id           TEXT          NOT NULL,
    shipping_limit_date TIMESTAMPTZ   NOT NULL,
    price               NUMERIC(12,2) NOT NULL,
    freight_value       NUMERIC(12,2) NOT NULL,
    _extracted_at       TIMESTAMPTZ   NOT NULL,
    _source             TEXT          NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.olist__order_reviews (
    review_id               TEXT        NOT NULL,
    order_id                TEXT        NOT NULL,
    review_score            SMALLINT    NOT NULL,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMPTZ NOT NULL,
    review_answer_timestamp TIMESTAMPTZ NOT NULL,
    _extracted_at           TIMESTAMPTZ NOT NULL,
    _source                 TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.olist__customers (
    customer_id              TEXT        NOT NULL,
    customer_unique_id       TEXT        NOT NULL,
    customer_zip_code_prefix TEXT        NOT NULL,
    customer_city            TEXT        NOT NULL,
    customer_state           CHAR(2)     NOT NULL,
    _extracted_at            TIMESTAMPTZ NOT NULL,
    _source                  TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze.olist__sellers (
    seller_id              TEXT        NOT NULL,
    seller_zip_code_prefix TEXT        NOT NULL,
    seller_city            TEXT        NOT NULL,
    seller_state           CHAR(2)     NOT NULL,
    _extracted_at          TIMESTAMPTZ NOT NULL,
    _source                TEXT        NOT NULL
);
