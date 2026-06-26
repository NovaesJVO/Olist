# SPEC 04: Staging dbt — 5 Models 1:1 com Bronze no Schema Silver

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Criar os 5 models de staging dbt que lêem as tabelas bronze, aplicam casting e renomeação de colunas, e materializam como views no schema `silver`. Sem regras de negócio — transformações de domínio ficam na camada intermediate.

---

## 2. Contexto

- **Pré-requisito**: SPEC 03 concluída — 5 tabelas bronze populadas em `bronze.*`
- **Projeto dbt**: `dbt_olist/` — profile `sertao_olist`, database `olist`
- **Próximo passo**: SPEC 05 (intermediate/marts — regras de negócio sobre silver)

---

## 3. Escopo

### 3.1 O que está incluso

- 5 models SQL em `dbt_olist/models/staging/`
- Arquivo de sources `_olist__sources.yml` declarando as 5 tabelas bronze
- Testes dbt: `unique`, `not_null`, `relationships` via sources file
- Macro `generate_schema_name` para output exato em `silver.*` (sem prefixo)
- Configuração de schema/materialization no `dbt_project.yml`

### 3.2 O que **não** está incluso

- Lógica de negócio (deduplicação, cálculo de métricas, joins)
- Models para geolocation, payments, products, category_name_translation
- Camadas intermediate ou marts

---

## 4. Decisões Técnicas

### 4.1 Schema: `silver`, materialização: `view`

**Decisão**: Todos os models de staging vão para o schema `silver` como views.

**Rationale**: Views não consomem espaço em disco e refletem sempre o estado atual de bronze. O schema `silver` está pré-criado pelo DDL da SPEC 02. A materialização como tabela só faz sentido em camadas com transformações pesadas (intermediate/marts).

### 4.2 Staging é 1:1 com bronze — sem regras de negócio

**Decisão**: Cada model de staging mapeia exatamente uma tabela bronze. Nenhum join, nenhum filtro de negócio, nenhuma agregação.

**Rationale**: A camada staging serve como contrato de tipos e nomes entre bronze (dados brutos) e as camadas superiores. Misturar lógica de negócio aqui quebraria a separação de responsabilidades e dificultaria debugging.

### 4.3 Schema literal `silver` via macro `generate_schema_name`

**Decisão**: Sobrescrever o macro padrão do dbt para usar o custom schema sem prefixo.

**Rationale**: O comportamento padrão do dbt concatena o schema do profile com o custom schema — resultando em `public_silver` em vez de `silver`. O macro abaixo corrige isso:

```sql
-- dbt_olist/macros/generate_schema_name.sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

### 4.4 Colunas `_extracted_at` e `_source` excluídas dos models

**Decisão**: As colunas de metadados de ingestão não são selecionadas nos models de staging.

**Rationale**: São metadados de pipeline, não dados de negócio. A camada silver expõe apenas colunas relevantes para análise. Os metadados permanecem acessíveis diretamente em bronze para auditoria.

---

## 5. Estrutura de Arquivos

```
dbt_olist/
├── dbt_project.yml          (atualizar: schema silver para staging)
├── macros/
│   └── generate_schema_name.sql   (novo)
└── models/
    └── staging/
        ├── _olist__sources.yml    (novo — declara bronze como source)
        ├── olist__orders.sql      (novo)
        ├── olist__order_items.sql (novo)
        ├── olist__order_reviews.sql (novo)
        ├── olist__customers.sql   (novo)
        └── olist__sellers.sql     (novo)
```

---

## 6. Configuração `dbt_project.yml`

```yaml
models:
  sertao_olist:
    +materialized: view
    staging:
      +schema: silver
```

---

## 7. Sources (`_olist__sources.yml`)

```yaml
version: 2

sources:
  - name: olist
    schema: bronze
    tables:
      - name: olist__orders
        columns:
          - name: order_id
            tests: [unique, not_null]
      - name: olist__order_items
        columns:
          - name: order_id
            tests: [not_null]
          - name: order_item_id
            tests: [not_null]
      - name: olist__order_reviews
        columns:
          - name: review_id
            tests: [unique, not_null]
      - name: olist__customers
        columns:
          - name: customer_id
            tests: [unique, not_null]
      - name: olist__sellers
        columns:
          - name: seller_id
            tests: [unique, not_null]
```

---

## 8. Especificação dos Models

### 8.1 `olist__orders.sql`

Source: `bronze.olist__orders`

| Coluna de entrada (bronze) | Coluna de saída (silver) | Tipo |
|---|---|---|
| `order_id` | `order_id` | TEXT |
| `customer_id` | `customer_id` | TEXT |
| `order_status` | `order_status` | TEXT |
| `order_purchase_timestamp` | `purchased_at` | TIMESTAMPTZ |
| `order_approved_at` | `approved_at` | TIMESTAMPTZ |
| `order_delivered_carrier_date` | `carrier_delivered_at` | TIMESTAMPTZ |
| `order_delivered_customer_date` | `customer_delivered_at` | TIMESTAMPTZ |
| `order_estimated_delivery_date` | `estimated_delivery_at` | TIMESTAMPTZ |

### 8.2 `olist__order_items.sql`

Source: `bronze.olist__order_items`

| Coluna de entrada (bronze) | Coluna de saída (silver) | Tipo |
|---|---|---|
| `order_id` | `order_id` | TEXT |
| `order_item_id` | `order_item_id` | INTEGER |
| `product_id` | `product_id` | TEXT |
| `seller_id` | `seller_id` | TEXT |
| `shipping_limit_date` | `shipping_limit_at` | TIMESTAMPTZ |
| `price` | `price` | NUMERIC(12,2) |
| `freight_value` | `freight_value` | NUMERIC(12,2) |

### 8.3 `olist__order_reviews.sql`

Source: `bronze.olist__order_reviews`

| Coluna de entrada (bronze) | Coluna de saída (silver) | Tipo |
|---|---|---|
| `review_id` | `review_id` | TEXT |
| `order_id` | `order_id` | TEXT |
| `review_score` | `review_score` | SMALLINT |
| `review_comment_title` | `comment_title` | TEXT |
| `review_comment_message` | `comment_message` | TEXT |
| `review_creation_date` | `created_at` | TIMESTAMPTZ |
| `review_answer_timestamp` | `answered_at` | TIMESTAMPTZ |

### 8.4 `olist__customers.sql`

Source: `bronze.olist__customers`

| Coluna de entrada (bronze) | Coluna de saída (silver) | Tipo |
|---|---|---|
| `customer_id` | `customer_id` | TEXT |
| `customer_unique_id` | `customer_unique_id` | TEXT |
| `customer_zip_code_prefix` | `zip_code_prefix` | TEXT |
| `customer_city` | `city` | TEXT |
| `customer_state` | `state` | CHAR(2) |

### 8.5 `olist__sellers.sql`

Source: `bronze.olist__sellers`

| Coluna de entrada (bronze) | Coluna de saída (silver) | Tipo |
|---|---|---|
| `seller_id` | `seller_id` | TEXT |
| `seller_zip_code_prefix` | `zip_code_prefix` | TEXT |
| `seller_city` | `city` | TEXT |
| `seller_state` | `state` | CHAR(2) |

---

## 9. Execução

### 9.1 Setup do profile (uma vez)

Copiar e ajustar o profile de exemplo:

```bash
cp dbt_olist/profiles.yml.example ~/.dbt/profiles.yml
```

### 9.2 Instalar dependências dbt

```bash
cd dbt_olist
dbt deps
```

### 9.3 Rodar os models de staging

```bash
cd dbt_olist
dbt run --select staging
```

### 9.4 Rodar os testes de sources

```bash
cd dbt_olist
dbt test --select staging
```

---

## 10. Critérios de Aceitação (DoD)

- [ ] `dbt run --select staging` conclui sem erros (5 views criadas)
- [ ] `SELECT * FROM silver.olist__orders LIMIT 10` retorna dados
- [ ] `SELECT * FROM silver.olist__order_items LIMIT 10` retorna dados
- [ ] `SELECT * FROM silver.olist__order_reviews LIMIT 10` retorna dados
- [ ] `SELECT * FROM silver.olist__customers LIMIT 10` retorna dados
- [ ] `SELECT * FROM silver.olist__sellers LIMIT 10` retorna dados
- [ ] Views estão em `silver.*` (não `public_silver.*`)
- [ ] Colunas renomeadas conforme seção 8 (ex: `purchased_at`, não `order_purchase_timestamp`)
- [ ] `_extracted_at` e `_source` ausentes nas views silver
- [ ] `dbt test --select staging` passa nos testes `unique` e `not_null`

---

## 11. Próximas Etapas

- **SPEC 05**: Intermediate — joins e regras de negócio sobre silver (ex: `int_orders_enriched`)
- **SPEC 06**: Marts gold — fatos e dimensões para consumo analítico

---

**Próxima Revisão**: Após implementação e validação do DoD  
**Responsável**: Novaes  
**Aprovação**: Pendente
