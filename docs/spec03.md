# SPEC 03: Ingestão ETL — Carga de CSVs nas Tabelas Bronze

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Carregar os CSVs de `dados_ajustados/` nas 5 tabelas bronze do PostgreSQL, adicionando automaticamente metadados de rastreabilidade (`_extracted_at`, `_source`) em cada linha.

---

## 2. Contexto

- **Pré-requisito**: SPEC 01B concluída — `dados_ajustados/` com timestamps deslocados (+2556 dias)
- **Pré-requisito**: SPEC 02 concluída — schemas `bronze`/`silver`/`gold` e tabelas tipadas existindo no Postgres
- **Script**: `ingestion/load_to_postgres.py` (aplica DDL se as tabelas ainda não existirem)
- **Próximo passo**: SPEC 04 (camada silver — limpeza e modelagem staging)

---

## 3. Escopo

### 3.1 O que está incluso

- Carga dos 5 CSVs nas tabelas bronze correspondentes
- Estratégia TRUNCATE + INSERT (carga completa e idempotente)
- Adição automática de metadados `_extracted_at` e `_source` em cada linha
- Aplicação do DDL se as tabelas ainda não existirem (bootstrap implícito)
- Validação de row counts pós-carga

### 3.2 O que **não** está incluso

- Carga dos demais CSVs (geolocation, payments, products, category_name_translation — escopo de spec futura)
- Data quality ou validação de nulos
- Carga incremental ou append-only
- Transformações de negócio (reservadas para a camada silver)

---

## 4. Decisões Técnicas

### 4.1 Estratégia de carga: TRUNCATE + INSERT

**Decisão**: Antes de cada carga, a tabela é truncada e recarregada integralmente.

**Rationale**: O dataset Olist é estático (Kaggle, transações de 2016–2018 deslocadas). Não há novas extrações recorrentes, portanto append incremental criaria complexidade desnecessária. A estratégia TRUNCATE garante idempotência completa — re-executar o script produz sempre o mesmo estado.

### 4.2 Metadados de rastreabilidade

**Decisão**: Duas colunas de metadados adicionadas automaticamente pelo script em cada linha carregada.

| Coluna | Tipo | Valor |
|--------|------|-------|
| `_extracted_at` | `TIMESTAMPTZ` | `now()` no momento da carga |
| `_source` | `TEXT` | Nome do arquivo CSV de origem (ex: `olist_orders_dataset.csv`) |

**Rationale**: Rastreabilidade mínima sem alterar os dados de negócio. Permite saber quando cada linha entrou no banco e de qual arquivo veio — útil para auditoria e reprocessamento seletivo.

### 4.3 Bootstrap implícito do DDL

**Decisão**: O script aplica `sql/ddl_bronze.sql` antes da carga se as tabelas não existirem.

**Rationale**: Permite rodar `load_to_postgres.py` standalone sem depender da execução prévia do pipeline Docker, facilitando desenvolvimento local.

### 4.4 Ferramenta de carga: `COPY FROM STDIN`

**Decisão**: Carga via `psycopg` (psycopg3) com `COPY FROM STDIN (FORMAT CSV)`.

**Rationale**: COPY é a forma mais eficiente de bulk insert no PostgreSQL — significativamente mais rápido que INSERT linha a linha. Streaming em chunks de 64 KB controla o uso de memória mesmo para tabelas grandes (>100 K linhas).

---

## 5. Mapeamento CSV → Tabela

| Arquivo CSV (`dados_ajustados/`) | Tabela Bronze | Linhas esperadas |
|----------------------------------|---------------|-----------------|
| `olist_orders_dataset.csv` | `bronze.olist__orders` | 99.441 |
| `olist_order_items_dataset.csv` | `bronze.olist__order_items` | 112.650 |
| `olist_order_reviews_dataset.csv` | `bronze.olist__order_reviews` | 99.224 |
| `olist_customers_dataset.csv` | `bronze.olist__customers` | 99.441 |
| `olist_sellers_dataset.csv` | `bronze.olist__sellers` | 3.095 |

**Total**: 413.851 linhas em 5 tabelas.

---

## 6. Interface do Script

### 6.1 Execução standalone

```bash
python ingestion/load_to_postgres.py --shifted-dir ./dados_ajustados
```

### 6.2 Variáveis de ambiente (conexão)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PG_HOST` | `localhost` | Host do PostgreSQL |
| `PG_PORT` | `5432` | Porta |
| `PG_DB` | `olist` | Database |
| `PG_USER` | `postgres` | Usuário |
| `PG_PASSWORD` | `postgres` | Senha |

### 6.3 Execução via pipeline Docker

O script é chamado automaticamente pelo passo `[4/4]` de `ingestion/pipeline.py` durante `docker compose up`.

### 6.4 Saída esperada

```
  ✅ bronze.olist__orders: 99,441 linhas
  ✅ bronze.olist__order_items: 112,650 linhas
  ✅ bronze.olist__order_reviews: 99,224 linhas
  ✅ bronze.olist__customers: 99,441 linhas
  ✅ bronze.olist__sellers: 3,095 linhas
```

---

## 7. Critérios de Aceitação (DoD)

- [ ] `SELECT count(*) FROM bronze.olist__orders` = **99.441**
- [ ] `SELECT count(*) FROM bronze.olist__order_items` = **112.650**
- [ ] `SELECT count(*) FROM bronze.olist__order_reviews` = **99.224**
- [ ] `SELECT count(*) FROM bronze.olist__customers` = **99.441**
- [ ] `SELECT count(*) FROM bronze.olist__sellers` = **3.095**
- [ ] Nenhuma tabela vazia
- [ ] Colunas `_extracted_at` e `_source` preenchidas em todas as linhas
- [ ] Re-execução do script não duplica dados (idempotente via TRUNCATE)
- [ ] Script funciona standalone (`python ingestion/load_to_postgres.py --shifted-dir ...`) sem necessidade do Docker

---

## 8. Próximas Etapas

- **SPEC 04**: DDL Silver — staging com limpeza de tipos, tratamento de nulos e renomeação de colunas
- **SPEC 05**: Ingestão Silver — transformações dbt sobre a camada bronze

---

**Próxima Revisão**: Após implementação e validação do DoD  
**Responsável**: Novaes  
**Aprovação**: Pendente
