# SPEC 02: DDL Bronze — Schemas e Tabelas Tipadas no PostgreSQL

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Criar os três schemas de camada (`bronze`, `silver`, `gold`) e as 5 tabelas bronze tipadas no PostgreSQL a partir do DDL em `sql/ddl_bronze.sql`. As tabelas recebem os dados brutos dos CSVs do Olist na etapa de carga (SPEC 03); nesta spec ficam apenas vazias e estruturadas.

---

## 2. Contexto

- **Pré-requisito**: SPEC 01 e SPEC 01B concluídas — CSVs disponíveis em `dados_ajustados/`
- **Próximo passo**: SPEC 03 (Ingestão ETL: carga CSV → tabelas bronze)
- **Arquitetura**: Medallion (bronze → silver → gold), implementada como schemas Postgres

---

## 3. Escopo

### 3.1 O que está incluso

- Criação dos schemas `bronze`, `silver`, `gold`
- Criação de 5 tabelas bronze com colunas tipadas
- Convenções de nomenclatura definidas

### 3.2 O que **não** está incluso

- Constraints de primary key ou foreign key (dados brutos não garantem integridade)
- Índices (definidos em etapas posteriores conforme padrão de acesso)
- Tabelas para os demais CSVs (geolocation, payments, products, category_name_translation — escopo de spec futura)
- Carga de dados (SPEC 03)

---

## 4. Decisões Técnicas

### 4.1 Schemas como camadas

**Decisão**: Cada camada da arquitetura medallion é um schema Postgres separado.

**Rationale**: Isola permissões por camada, evita colisão de nomes entre camadas, e permite `GRANT` diferenciado por role (ex.: analistas lêem apenas `gold`).

### 4.2 Convenção de nomenclatura

**Padrão**: `<schema>.<dominio>__<entidade>` (duplo underscore separa domínio de entidade)

| Camada | Tabela                           |
|--------|----------------------------------|
| bronze | `bronze.olist__orders`           |
| bronze | `bronze.olist__order_items`      |
| bronze | `bronze.olist__order_reviews`    |
| bronze | `bronze.olist__customers`        |
| bronze | `bronze.olist__sellers`          |

**Rationale**: Duplo underscore é convenção dbt para tabelas geradas; usá-lo aqui cria consistência visual e evita ambiguidade com underscores internos ao nome da entidade.

### 4.3 Tipos de dados

| Tipo Postgres   | Uso                                          |
|-----------------|----------------------------------------------|
| `TEXT`          | IDs e strings sem tamanho fixo               |
| `CHAR(2)`       | Código de UF (estado brasileiro — sempre 2 chars) |
| `TIMESTAMPTZ`   | Todos os timestamps (preserva fuso horário)  |
| `NUMERIC(12,2)` | Valores monetários (price, freight_value)    |
| `INTEGER`       | Sequências inteiras (order_item_id)          |
| `SMALLINT`      | review_score (1–5, economiza espaço)         |

### 4.4 Nullability

Colunas anuláveis refletem a realidade do dataset:

- `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`: pedidos podem ser cancelados antes dessas etapas
- `review_comment_title`, `review_comment_message`: campos opcionais no formulário

---

## 5. Especificação das Tabelas

### 5.1 `bronze.olist__orders`

Fonte: `olist_orders_dataset.csv`

| Coluna                        | Tipo        | Null? |
|-------------------------------|-------------|-------|
| `order_id`                    | TEXT        | NOT NULL |
| `customer_id`                 | TEXT        | NOT NULL |
| `order_status`                | TEXT        | NOT NULL |
| `order_purchase_timestamp`    | TIMESTAMPTZ | NOT NULL |
| `order_approved_at`           | TIMESTAMPTZ | NULL |
| `order_delivered_carrier_date`| TIMESTAMPTZ | NULL |
| `order_delivered_customer_date`| TIMESTAMPTZ| NULL |
| `order_estimated_delivery_date`| TIMESTAMPTZ| NOT NULL |

### 5.2 `bronze.olist__order_items`

Fonte: `olist_order_items_dataset.csv`

| Coluna               | Tipo           | Null? |
|----------------------|----------------|-------|
| `order_id`           | TEXT           | NOT NULL |
| `order_item_id`      | INTEGER        | NOT NULL |
| `product_id`         | TEXT           | NOT NULL |
| `seller_id`          | TEXT           | NOT NULL |
| `shipping_limit_date`| TIMESTAMPTZ    | NOT NULL |
| `price`              | NUMERIC(12,2)  | NOT NULL |
| `freight_value`      | NUMERIC(12,2)  | NOT NULL |

### 5.3 `bronze.olist__order_reviews`

Fonte: `olist_order_reviews_dataset.csv`

| Coluna                   | Tipo        | Null? |
|--------------------------|-------------|-------|
| `review_id`              | TEXT        | NOT NULL |
| `order_id`               | TEXT        | NOT NULL |
| `review_score`           | SMALLINT    | NOT NULL |
| `review_comment_title`   | TEXT        | NULL |
| `review_comment_message` | TEXT        | NULL |
| `review_creation_date`   | TIMESTAMPTZ | NOT NULL |
| `review_answer_timestamp`| TIMESTAMPTZ | NOT NULL |

### 5.4 `bronze.olist__customers`

Fonte: `olist_customers_dataset.csv`

| Coluna                    | Tipo    | Null? |
|---------------------------|---------|-------|
| `customer_id`             | TEXT    | NOT NULL |
| `customer_unique_id`      | TEXT    | NOT NULL |
| `customer_zip_code_prefix`| TEXT    | NOT NULL |
| `customer_city`           | TEXT    | NOT NULL |
| `customer_state`          | CHAR(2) | NOT NULL |

### 5.5 `bronze.olist__sellers`

Fonte: `olist_sellers_dataset.csv`

| Coluna                  | Tipo    | Null? |
|-------------------------|---------|-------|
| `seller_id`             | TEXT    | NOT NULL |
| `seller_zip_code_prefix`| TEXT    | NOT NULL |
| `seller_city`           | TEXT    | NOT NULL |
| `seller_state`          | CHAR(2) | NOT NULL |

---

## 6. Implementação

### 6.1 Pré-requisito

```bash
docker compose up -d
```

### 6.2 Executar o DDL

```bash
psql -h localhost -U postgres -d olist -f sql/ddl_bronze.sql
```

Ou via `docker exec`:

```bash
docker exec -i $(docker compose ps -q postgres) \
  psql -U postgres -d olist < sql/ddl_bronze.sql
```

### 6.3 Arquivo DDL

`sql/ddl_bronze.sql` — cria os 3 schemas e as 5 tabelas com `CREATE ... IF NOT EXISTS` (idempotente; seguro para re-executar).

---

## 7. Critérios de Aceitação (DoD)

- [ ] `\dn` no psql lista `bronze`, `silver` e `gold`
- [ ] `\dt bronze.*` lista exatamente 5 tabelas:
  - `bronze.olist__orders`
  - `bronze.olist__order_items`
  - `bronze.olist__order_reviews`
  - `bronze.olist__customers`
  - `bronze.olist__sellers`
- [ ] Todas as 5 tabelas estão **vazias** (`SELECT count(*) = 0`)
- [ ] `sql/ddl_bronze.sql` é idempotente (segunda execução não gera erros)
- [ ] Tipos conferem: `TIMESTAMPTZ` em timestamps, `NUMERIC(12,2)` em valores, `CHAR(2)` em UFs

---

## 8. Próximas Etapas

- **SPEC 03**: Ingestão ETL — carregar `dados_ajustados/` nas tabelas bronze via Python (`ingestion/load_to_postgres.py`)
- **SPEC 04**: DDL Silver — modelagem staging com limpeza e tipagem refinada
- **SPEC 05**: DDL Gold — marts dimensionais (fatos e dimensões)

---

**Próxima Revisão**: Após execução e validação do DoD  
**Responsável**: Novaes  
**Aprovação**: Pendente
