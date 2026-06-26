# SPEC 07: Testes Automatizados dbt — Sources, Marts e Sanity Check

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Garantir qualidade dos dados via testes automatizados antes de liberar os marts para consumo no dashboard. Cobre integridade estrutural (unique, not_null, relationships) e um sanity check de negócio contra artefatos do date shift.

---

## 2. Contexto

- **Pré-requisito**: SPECs 04–06 concluídas — staging, intermediate e marts disponíveis
- **Testes existentes**: `_olist__sources.yml` já tem `unique`/`not_null` nas PKs das 5 tabelas bronze (SPEC 04)
- **Novos artefatos**: `_ecommerce__marts.yml` (testes nos 4 marts) + `assert_no_negative_lead_time.sql` (teste singular)

---

## 3. Escopo

### 3.1 O que está incluso

- Testes genéricos nos 4 marts via `_ecommerce__marts.yml`
- 1 teste singular em `tests/assert_no_negative_lead_time.sql`
- Execução completa via `dbt test`

### 3.2 O que **não** está incluso

- Testes nos models intermediate ou staging (validações de negócio ficam nos marts)
- Testes de `accepted_values` (exigiria manutenção constante com dataset estático)
- Testes de `freshness` (dataset Kaggle, sem ingestão incremental)

---

## 4. Decisões Técnicas

### 4.1 Testes genéricos por camada

**Decisão**: Testes de `unique` e `not_null` apenas nas PKs dos marts, não em todas as colunas.

**Rationale**: Testar nullability em colunas opcionais (ex: `seller_id` quando `multi_vendedor = true`) geraria falsos positivos. O foco é garantir integridade das chaves de junção que ferramentas BI usarão.

### 4.2 `relationships` apenas onde há garantia de integridade

**Decisão**: Não adicionar testes de `relationships` entre marts (ex: `ecommerce__pedidos.seller_id → ecommerce__vendedores.seller_id`).

**Rationale**: `ecommerce__pedidos` inclui pedidos com `seller_id = NULL` (multi_vendedor) — um `relationships` falharia. A integridade referencial é responsabilidade do intermediate, não do mart de consumo.

### 4.3 Teste singular: `assert_no_negative_lead_time`

**Decisão**: Teste SQL que falha se qualquer pedido entregue tiver `lead_time_total_dias < 0` (`customer_delivered_at < purchased_at`).

**Rationale**: Lead time negativo seria evidência de erro no date shift (SPEC 01B) — o deslocamento de datas poderia ter criado inconsistências se aplicado de forma não-uniforme entre colunas. Este sanity check protege contra essa classe de bug. Em dbt, testes singulares falham quando a query retorna **qualquer linha** — logo, a query retorna pedidos com lead time negativo.

---

## 5. Especificação dos Testes

### 5.1 Testes genéricos — `_ecommerce__marts.yml`

#### `ecommerce__pedidos`

| Coluna | Testes |
|---|---|
| `order_id` | `unique`, `not_null` |
| `customer_id` | `not_null` |
| `purchased_at` | `not_null` |

#### `ecommerce__vendedores`

| Coluna | Testes |
|---|---|
| `seller_id` | `unique`, `not_null` |
| `total_pedidos` | `not_null` |
| `receita_produtos` | `not_null` |

#### `ecommerce__geografia`

| Coluna | Testes |
|---|---|
| `customer_state` | `unique`, `not_null` |
| `total_pedidos` | `not_null` |

#### `ecommerce__visao_executiva`

| Coluna | Testes |
|---|---|
| `mes` | `unique`, `not_null` |
| `total_pedidos` | `not_null` |

### 5.2 Teste singular — `tests/assert_no_negative_lead_time.sql`

```sql
-- Falha se qualquer pedido entregue tiver entrega antes da compra.
-- Sanity check contra inconsistências do date shift (SPEC 01B).
select *
from {{ ref('ecommerce__pedidos') }}
where lead_time_total_dias < 0
```

Retornar 0 linhas = **PASS**. Qualquer linha = **FAIL**.

---

## 6. Execução

```bash
cd dbt_olist
dbt test --profiles-dir .
```

Para rodar apenas os testes dos marts:

```bash
dbt test --select marts --profiles-dir .
```

Para rodar apenas o teste singular:

```bash
dbt test --select assert_no_negative_lead_time --profiles-dir .
```

---

## 7. Critérios de Aceitação (DoD)

- [ ] `dbt test` conclui com **0 falhas**
- [ ] Testes de `unique` passam em `order_id`, `seller_id`, `customer_state`, `mes`
- [ ] Testes de `not_null` passam em todas as colunas configuradas
- [ ] `assert_no_negative_lead_time` retorna **0 linhas** (PASS)
- [ ] Total de testes executados ≥ 25 (19 de sources + novos de marts + singular)

---

## 8. Próximas Etapas

- **SPEC 08**: Conexão de ferramenta BI aos 4 marts gold

---

**Próxima Revisão**: Após execução e validação  
**Responsável**: Novaes  
**Aprovação**: Pendente
