# SPEC 08: Integração E2E — Pipeline Completo do Zero

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Executar e validar o fluxo completo do pipeline desde o arquivo bruto até os marts gold, sem intervenção manual além de dois comandos. Confirmar que cada camada produz exatamente o esperado e que as contagens são consistentes entre si.

---

## 2. Contexto

- **Pré-requisito**: `archive.zip` presente na raiz do projeto
- **Cobre**: todas as SPECs anteriores (01 a 07) rodando em sequência
- **Objetivo final**: demonstrar reproduzibilidade completa do pipeline — qualquer pessoa com o repositório e o `archive.zip` reproduz os resultados

---

## 3. Fluxo Completo

```
archive.zip
    │
    ▼ [1] docker compose up --build
    ├── unzip → dados_originais/ (9 CSVs)
    ├── date shift +2556 dias → dados_ajustados/ (3 arquivos alterados)
    ├── CREATE SCHEMA bronze/silver/gold + 5 tabelas (DDL)
    └── COPY CSVs → bronze.* (5 tabelas)
    │
    ▼ [2] dbt build
    ├── staging   → 5 views  em silver.*  (renomeação de colunas)
    ├── intermediate → 1 view em silver.* (joins + métricas)
    ├── marts     → 4 tables em gold.*    (filtros + agregações)
    └── tests     → 33 testes             (0 falhas)
```

---

## 4. Decisões Técnicas

### 4.1 `dbt build` em vez de `dbt run + dbt test`

**Decisão**: Usar `dbt build` como único comando dbt da validação E2E.

**Rationale**: `dbt build` executa modelos e testes na ordem topológica correta — testa cada nó antes de materializá-lo como dependência dos próximos. Falhas são detectadas o mais cedo possível, sem rodar transformações pesadas sobre dados corrompidos.

### 4.2 Volume Docker limpo obrigatório (`-v`)

**Decisão**: O E2E sempre usa `docker compose down -v` antes, para garantir que o Postgres é recriado do zero.

**Rationale**: Um volume existente pode conter dados de uma execução anterior com schema diferente (ex: sem as colunas `_extracted_at`/`_source` adicionadas na SPEC 03). Partir de um volume limpo elimina essa classe de inconsistência.

---

## 5. Comandos

### 5.1 Passo 1 — Pipeline de dados

```bash
docker compose down -v
docker compose up --build
```

Aguardar `pipeline-1 exited with code 0` antes de prosseguir.

### 5.2 Passo 2 — Transformações e testes dbt

```bash
cd dbt_olist
dbt build --profiles-dir .
```

---

## 6. Contagens Esperadas por Camada

### Bronze (após docker compose up)

| Tabela | Linhas |
|---|---|
| `bronze.olist__orders` | 99.441 |
| `bronze.olist__order_items` | 112.650 |
| `bronze.olist__order_reviews` | 99.224 |
| `bronze.olist__customers` | 99.441 |
| `bronze.olist__sellers` | 3.095 |
| **Total** | **413.851** |

### Silver (após dbt build)

| Model | Tipo | Linhas |
|---|---|---|
| `silver.olist__orders` | view | 99.441 |
| `silver.olist__order_items` | view | 112.650 |
| `silver.olist__order_reviews` | view | 99.224 |
| `silver.olist__customers` | view | 99.441 |
| `silver.olist__sellers` | view | 3.095 |
| `silver.intermediate__pedidos_enriquecidos` | view | 99.441 |

### Gold (após dbt build)

| Mart | Tipo | Linhas |
|---|---|---|
| `gold.ecommerce__pedidos` | table | 96.478 |
| `gold.ecommerce__vendedores` | table | 2.948 |
| `gold.ecommerce__geografia` | table | 27 |
| `gold.ecommerce__visao_executiva` | table | 23 |

### Consistência entre camadas

| Verificação | Esperado |
|---|---|
| `bronze.olist__orders` = `silver.olist__orders` | 99.441 = 99.441 |
| `silver.olist__orders` = `silver.intermediate__pedidos_enriquecidos` | 99.441 = 99.441 |
| `gold.ecommerce__pedidos` < `silver.olist__orders` | 96.478 < 99.441 (filtro `delivered`) |
| `gold.ecommerce__geografia` | 27 (todos os estados brasileiros) |

---

## 7. Validação do Date Shift

```sql
-- Período esperado: set/2023 a out/2025
SELECT
    MIN(purchased_at)::date AS data_minima,
    MAX(purchased_at)::date AS data_maxima
FROM gold.ecommerce__pedidos;
-- data_minima: ~2023-09-04
-- data_maxima: ~2025-08-xx
```

---

## 8. Query de Validação Completa

```sql
SELECT
    'bronze.olist__orders'                          AS tabela, count(*) AS linhas FROM bronze.olist__orders
UNION ALL SELECT 'bronze.olist__order_items',       count(*) FROM bronze.olist__order_items
UNION ALL SELECT 'bronze.olist__order_reviews',     count(*) FROM bronze.olist__order_reviews
UNION ALL SELECT 'bronze.olist__customers',         count(*) FROM bronze.olist__customers
UNION ALL SELECT 'bronze.olist__sellers',           count(*) FROM bronze.olist__sellers
UNION ALL SELECT 'silver.int__pedidos_enriquecidos',count(*) FROM silver.intermediate__pedidos_enriquecidos
UNION ALL SELECT 'gold.ecommerce__pedidos',         count(*) FROM gold.ecommerce__pedidos
UNION ALL SELECT 'gold.ecommerce__vendedores',      count(*) FROM gold.ecommerce__vendedores
UNION ALL SELECT 'gold.ecommerce__geografia',       count(*) FROM gold.ecommerce__geografia
UNION ALL SELECT 'gold.ecommerce__visao_executiva', count(*) FROM gold.ecommerce__visao_executiva
ORDER BY tabela;
```

---

## 9. Critérios de Aceitação (DoD)

- [ ] `docker compose up --build` conclui com `pipeline-1 exited with code 0`
- [ ] `dbt build` conclui com `PASS=33 WARN=0 ERROR=0`
- [ ] Contagens bronze batem com os valores da seção 6
- [ ] `silver.intermediate__pedidos_enriquecidos` = 99.441 (= `bronze.olist__orders`)
- [ ] `gold.ecommerce__pedidos` = 96.478 (< 99.441 — filtro `delivered`)
- [ ] `gold.ecommerce__geografia` = 27 UFs
- [ ] `MIN(purchased_at)` em `gold.ecommerce__pedidos` ≥ `2023-09-01`
- [ ] `MAX(purchased_at)` em `gold.ecommerce__pedidos` ≤ `2025-10-31`
- [ ] Segunda execução (`down -v + up + dbt build`) produz os mesmos resultados

---

**Próxima Revisão**: Após execução e validação  
**Responsável**: Novaes  
**Aprovação**: Pendente
