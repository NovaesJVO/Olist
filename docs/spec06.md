# SPEC 06: Marts Gold — 4 Tabelas de Consumo para Dashboard

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Criar os 4 marts de consumo no schema `gold` (tabelas físicas), prontos para conexão com ferramenta de BI. Cada mart responde a uma perspectiva analítica diferente do dataset Olist.

---

## 2. Contexto

- **Pré-requisito**: SPEC 05 concluída — `silver.intermediate__pedidos_enriquecidos` disponível (99.441 linhas, grão = pedido)
- **Schema**: `gold`, materialização `table` (não view — BI conecta diretamente)
- **Fonte única**: todos os marts lêem de `intermediate__pedidos_enriquecidos`
- **Próximo passo**: conexão de ferramenta BI (Power BI / Metabase)

---

## 3. Escopo

### 3.1 O que está incluso

- 4 marts com grãos e filtros distintos
- Configuração `+schema: gold` e `+materialized: table` no `dbt_project.yml`

### 3.2 O que **não** está incluso

- Marts de produtos, pagamentos ou geolocalização
- Filtros de data parametrizáveis (o dataset é estático)
- Testes dbt sobre os marts (validações estão no intermediate)

---

## 4. Decisões Técnicas

### 4.1 Materialização: table

**Decisão**: Marts são materializados como tabelas físicas no schema `gold`.

**Rationale**: Ferramentas BI (Power BI, Metabase) performam melhor lendo tabelas do que recalculando views com joins pesados. A atualização ocorre via `dbt run`, não em tempo real.

### 4.2 Filtro de pedidos: apenas `delivered`

**Decisão**: `ecommerce__pedidos` e todos os marts agregados filtram `order_status = 'delivered'`.

**Rationale**: Só pedidos entregues têm os campos de tempo (`customer_delivered_at`) preenchidos. Incluir outros status criaria nulls em métricas de atraso e lead time, distorcendo médias.

### 4.3 `ecommerce__vendedores` exclui `multi_vendedor = true`

**Decisão**: O mart de vendedores filtra pedidos com múltiplos vendedores.

**Rationale**: Como documentado na SPEC 05, `seller_id` é `NULL` para esses pedidos. Incluí-los no mart de performance por vendedor seria impossível e incorreto.

### 4.4 Recorte interestadual em `ecommerce__geografia`

**Decisão**: Flag `interestadual = (seller_state IS DISTINCT FROM customer_state AND seller_state IS NOT NULL)`.

**Rationale**: Entregas interestaduais tendem a ter maior lead time e maior risco de atraso — é uma dimensão analítica relevante para o negócio. Pedidos multi-vendedor (sem `seller_state`) ficam como `NULL` nessa flag.

### 4.5 Série mensal em `ecommerce__visao_executiva`

**Decisão**: Truncar `purchased_at` por mês (`date_trunc('month', purchased_at)`). Período esperado: set/2023 a out/2025.

**Rationale**: O dataset original (2016–2018) foi deslocado +2556 dias (SPEC 01B), resultando nesse intervalo. A série mensal é o recorte mais natural para visão executiva de e-commerce.

---

## 5. Especificação dos Marts

### 5.1 `ecommerce__pedidos`

**Grão**: 1 linha por pedido entregue  
**Filtro**: `order_status = 'delivered'`

| Coluna | Tipo | Descrição |
|---|---|---|
| `order_id` | TEXT | PK |
| `customer_id` | TEXT | |
| `customer_unique_id` | TEXT | |
| `customer_state` | CHAR(2) | UF do cliente |
| `seller_id` | TEXT | NULL se multi_vendedor |
| `seller_state` | CHAR(2) | UF do vendedor |
| `multi_vendedor` | BOOLEAN | |
| `qtd_itens` | INTEGER | |
| `valor_produtos` | NUMERIC | |
| `valor_frete` | NUMERIC | |
| `review_score` | SMALLINT | |
| `purchased_at` | TIMESTAMPTZ | |
| `customer_delivered_at` | TIMESTAMPTZ | |
| `tempo_aprovacao_dias` | NUMERIC | |
| `tempo_postagem_dias` | NUMERIC | |
| `tempo_transporte_dias` | NUMERIC | |
| `lead_time_total_dias` | NUMERIC | |
| `atraso_entrega_dias` | NUMERIC | |
| `atrasado` | BOOLEAN | |
| `nota_baixa` | BOOLEAN | |

---

### 5.2 `ecommerce__vendedores`

**Grão**: 1 linha por vendedor  
**Filtros**: `order_status = 'delivered'` AND `multi_vendedor = false`

| Coluna | Tipo | Descrição |
|---|---|---|
| `seller_id` | TEXT | PK |
| `seller_state` | CHAR(2) | |
| `total_pedidos` | BIGINT | |
| `total_itens` | BIGINT | |
| `receita_produtos` | NUMERIC | `SUM(valor_produtos)` |
| `receita_frete` | NUMERIC | `SUM(valor_frete)` |
| `ticket_medio` | NUMERIC | `AVG(valor_produtos)` |
| `lead_time_medio_dias` | NUMERIC | `AVG(lead_time_total_dias)` |
| `pct_atrasado` | NUMERIC | `AVG(atrasado::int) * 100` |
| `nota_media` | NUMERIC | `AVG(review_score)` |
| `pct_nota_baixa` | NUMERIC | `AVG(nota_baixa::int) * 100` |
| `ranking_receita` | BIGINT | `RANK() OVER (ORDER BY receita_produtos DESC)` |

---

### 5.3 `ecommerce__geografia`

**Grão**: 1 linha por UF do cliente  
**Filtro**: `order_status = 'delivered'`

| Coluna | Tipo | Descrição |
|---|---|---|
| `customer_state` | CHAR(2) | PK |
| `total_pedidos` | BIGINT | |
| `pct_interestadual` | NUMERIC | % de pedidos com seller_state ≠ customer_state |
| `lead_time_medio_dias` | NUMERIC | |
| `atraso_medio_dias` | NUMERIC | `AVG(atraso_entrega_dias)` |
| `pct_atrasado` | NUMERIC | `AVG(atrasado::int) * 100` |
| `nota_media` | NUMERIC | |
| `pct_nota_baixa` | NUMERIC | |
| `receita_total` | NUMERIC | `SUM(valor_produtos + valor_frete)` |

---

### 5.4 `ecommerce__visao_executiva`

**Grão**: 1 linha por mês  
**Filtro**: `order_status = 'delivered'`  
**Período esperado**: set/2023 → out/2025 (25 meses)

| Coluna | Tipo | Descrição |
|---|---|---|
| `mes` | DATE | `date_trunc('month', purchased_at)` |
| `total_pedidos` | BIGINT | |
| `receita_produtos` | NUMERIC | `SUM(valor_produtos)` |
| `receita_frete` | NUMERIC | `SUM(valor_frete)` |
| `ticket_medio` | NUMERIC | `AVG(valor_produtos)` |
| `lead_time_medio_dias` | NUMERIC | |
| `pct_atrasado` | NUMERIC | `AVG(atrasado::int) * 100` |
| `nota_media` | NUMERIC | `AVG(review_score)` |
| `pct_nota_baixa` | NUMERIC | `AVG(nota_baixa::int) * 100` |

---

## 6. Execução

```bash
cd dbt_olist
dbt run --select marts --profiles-dir .
```

---

## 7. Critérios de Aceitação (DoD)

- [ ] `dbt run --select marts` conclui sem erros (4 tabelas criadas)
- [ ] `SELECT count(*) FROM gold.ecommerce__pedidos` > 0 (apenas pedidos `delivered`)
- [ ] `SELECT count(*) FROM gold.ecommerce__vendedores` > 0
- [ ] `SELECT count(*) FROM gold.ecommerce__geografia` = 27 (26 estados + DF)
- [ ] `SELECT count(*) FROM gold.ecommerce__visao_executiva` ≈ 25 (set/2023 a out/2025)
- [ ] `ecommerce__visao_executiva`: `MIN(mes) >= '2023-09-01'` e `MAX(mes) <= '2025-10-31'`
- [ ] `ecommerce__vendedores`: `ranking_receita = 1` para o vendedor com maior receita

---

## 8. Próximas Etapas

- **SPEC 07**: Conexão de ferramenta BI (Power BI / Metabase) consumindo os 4 marts gold

---

**Próxima Revisão**: Após implementação e validação do DoD  
**Responsável**: Novaes  
**Aprovação**: Pendente
