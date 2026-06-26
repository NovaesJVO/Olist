# SPEC 05: Intermediate — `intermediate__pedidos_enriquecidos`

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Criar o model intermediate que consolida dados de pedidos, clientes, itens, vendedores e reviews num único grão de pedido, calculando métricas de tempo e atraso de entrega.

---

## 2. Contexto

- **Pré-requisito**: SPEC 04 concluída — 5 views staging disponíveis em `silver.*`
- **Grão**: 1 linha por `order_id`
- **Artefato**: `dbt_olist/models/intermediate/intermediate__pedidos_enriquecidos.sql`
- **Próximo passo**: SPEC 06 (mart gold — exposição analítica deste intermediate)

---

## 3. Escopo

### 3.1 O que está incluso

- Join entre as 5 tabelas staging
- Resolução de pedidos com múltiplos vendedores (flag `multi_vendedor`)
- Deduplicação de reviews (fica a mais recente por pedido)
- 7 métricas derivadas de tempo/atraso
- Materialização: view no schema `silver`

### 3.2 O que **não** está incluso

- Dados de geolocation, payments, products (escopo de spec futura)
- Agregações por cliente, vendedor ou período (reservadas para marts gold)
- Filtros de negócio (ex: excluir cancelados) — decisão da camada gold

---

## 4. Decisões Técnicas

### 4.1 Grão: 1 linha por pedido

**Decisão**: O model tem exatamente uma linha por `order_id`, mesmo que o pedido tenha múltiplos itens, vendedores ou reviews.

**Rationale**: O grão de pedido é a unidade de análise mais natural para métricas de fulfillment (tempo de entrega, atraso). Métricas por item ficam em models separados.

### 4.2 Pedidos com múltiplos vendedores

**Decisão**: Quando um pedido tem itens de mais de um vendedor, `seller_id` e `seller_state` ficam `NULL` e a flag `multi_vendedor = true`.

**Rationale**: A data de entrega é registrada por pedido, não por vendedor. Atribuir a entrega a um único vendedor quando há vários seria arbitrário e enganoso para análises de performance por vendedor.

### 4.3 Reviews duplicadas

**Decisão**: Se um pedido tem mais de uma review, fica a mais recente (`answered_at` DESC).

**Rationale**: Reviews duplicadas são ruído do dataset. A mais recente representa o estado final da avaliação do cliente.

### 4.4 Métricas de tempo

Todas as métricas são calculadas em **dias** (decimais) com `EXTRACT(EPOCH FROM ...)/ 86400.0`.

| Métrica | Cálculo | Interpretação |
|---|---|---|
| `tempo_aprovacao_dias` | `approved_at - purchased_at` | Tempo até aprovação do pagamento |
| `tempo_postagem_dias` | `carrier_delivered_at - approved_at` | Tempo do seller postar após aprovação |
| `tempo_transporte_dias` | `customer_delivered_at - carrier_delivered_at` | Tempo em trânsito |
| `lead_time_total_dias` | `customer_delivered_at - purchased_at` | Tempo total do ciclo do pedido |
| `atraso_entrega_dias` | `customer_delivered_at - estimated_delivery_at` | Positivo = atrasado, negativo = adiantado |
| `atrasado` | `atraso_entrega_dias > 0` | Flag booleana de atraso |
| `nota_baixa` | `review_score <= 2` | Flag para NPS negativo |

**Nulls**: Métricas que dependem de `customer_delivered_at` são `NULL` para pedidos não entregues (cancelados, em trânsito).

---

## 5. Joins e Lógica

### 5.1 Estrutura do model

```
silver.olist__orders          (âncora — 1 linha por pedido)
  LEFT JOIN silver.olist__customers   ON customer_id
  LEFT JOIN itens_por_pedido          ON order_id    ← CTE com agregação
  LEFT JOIN silver.olist__sellers     ON seller_id   ← NULL se multi_vendedor
  LEFT JOIN review_mais_recente       ON order_id    ← CTE com deduplicação
```

### 5.2 CTE `itens_por_pedido`

Agrega `silver.olist__order_items` por `order_id`:
- `COUNT(DISTINCT seller_id)` → detecta `multi_vendedor`
- `SUM(price)` → `valor_produtos`
- `SUM(freight_value)` → `valor_frete`
- `COUNT(order_item_id)` → `qtd_itens`
- `seller_id` → `NULL` se `COUNT(DISTINCT seller_id) > 1`

### 5.3 CTE `review_mais_recente`

```sql
ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY answered_at DESC) = 1
```

---

## 6. Schema de Saída

| Coluna | Tipo | Fonte / Cálculo |
|---|---|---|
| `order_id` | TEXT | `orders.order_id` |
| `customer_id` | TEXT | `orders.customer_id` |
| `customer_unique_id` | TEXT | `customers.customer_unique_id` |
| `customer_state` | CHAR(2) | `customers.state` |
| `order_status` | TEXT | `orders.order_status` |
| `purchased_at` | TIMESTAMPTZ | `orders.purchased_at` |
| `approved_at` | TIMESTAMPTZ | `orders.approved_at` |
| `carrier_delivered_at` | TIMESTAMPTZ | `orders.carrier_delivered_at` |
| `customer_delivered_at` | TIMESTAMPTZ | `orders.customer_delivered_at` |
| `estimated_delivery_at` | TIMESTAMPTZ | `orders.estimated_delivery_at` |
| `seller_id` | TEXT | `items.seller_id` (NULL se multi_vendedor) |
| `seller_state` | CHAR(2) | `sellers.state` (NULL se multi_vendedor) |
| `multi_vendedor` | BOOLEAN | `COUNT(DISTINCT seller_id) > 1` |
| `qtd_itens` | INTEGER | `COUNT(order_item_id)` |
| `valor_produtos` | NUMERIC | `SUM(price)` |
| `valor_frete` | NUMERIC | `SUM(freight_value)` |
| `review_score` | SMALLINT | `reviews.review_score` |
| `review_answered_at` | TIMESTAMPTZ | `reviews.answered_at` |
| `tempo_aprovacao_dias` | NUMERIC | `approved_at - purchased_at` |
| `tempo_postagem_dias` | NUMERIC | `carrier_delivered_at - approved_at` |
| `tempo_transporte_dias` | NUMERIC | `customer_delivered_at - carrier_delivered_at` |
| `lead_time_total_dias` | NUMERIC | `customer_delivered_at - purchased_at` |
| `atraso_entrega_dias` | NUMERIC | `customer_delivered_at - estimated_delivery_at` |
| `atrasado` | BOOLEAN | `atraso_entrega_dias > 0` |
| `nota_baixa` | BOOLEAN | `review_score <= 2` |

---

## 7. Execução

```bash
cd dbt_olist
dbt run --select intermediate --profiles-dir .
```

---

## 8. Critérios de Aceitação (DoD)

- [ ] `dbt run --select intermediate` conclui sem erros
- [ ] `SELECT count(*) FROM silver.intermediate__pedidos_enriquecidos` = `SELECT count(*) FROM silver.olist__orders` (99.441)
- [ ] Pedidos com `multi_vendedor = true` têm `seller_id IS NULL`
- [ ] `atraso_entrega_dias > 0` ↔ `atrasado = true` (consistência)
- [ ] Pedidos não entregues têm `lead_time_total_dias IS NULL`
- [ ] `nota_baixa = true` apenas quando `review_score <= 2`

---

## 9. Próximas Etapas

- **SPEC 06**: Mart gold — `mart__performance_vendedores` e `mart__satisfacao_clientes` consumindo este intermediate

---

**Próxima Revisão**: Após implementação e validação do DoD  
**Responsável**: Novaes  
**Aprovação**: Pendente
