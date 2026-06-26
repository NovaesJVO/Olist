# SPEC 11: Documentação dbt — Catálogo Navegável via dbt docs

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Documentar todos os models dbt (staging, intermediate, marts) com descrição de tabela e de cada coluna, gerando um catálogo navegável via `dbt docs serve`. Toda FK fica documentada com descrição explícita e teste `relationships`.

---

## 2. Contexto

- **Pré-requisito**: SPECs 04–07 concluídas — modelos existentes e testados
- **Substitui**: o catálogo YAML em `catalog/` (SPEC 09) para o escopo dbt — aqui a documentação fica integrada ao próprio projeto dbt, coluna a coluna
- **Geração**: `dbt docs generate && dbt docs serve` — sem ferramenta externa

---

## 3. Arquivos a Criar / Expandir

| Arquivo | Ação | Conteúdo |
|---|---|---|
| `models/staging/_olist__staging.yml` | **NOVO** | 5 models staging, coluna a coluna, testes FK |
| `models/intermediate/_intermediate__models.yml` | **NOVO** | 1 model intermediate, 25 colunas, FK relationships |
| `models/marts/_ecommerce__marts.yml` | **EXPANDIR** | Adicionar descrição a todas as colunas dos 4 marts |

---

## 4. Decisões Técnicas

### 4.1 Documentação ao lado dos models (não em arquivo central)

**Decisão**: Um `.yml` por camada, dentro da própria pasta do model.

**Rationale**: Colocação padrão dbt — `dbt docs generate` encontra automaticamente. Facilita manutenção ao editar um model: doc e SQL ficam na mesma pasta.

### 4.2 FK documentada em dois lugares

**Decisão**: Toda chave estrangeira recebe (1) descrição no formato `"FK para <model>.<coluna>"` + (2) teste `relationships` na coluna.

**Rationale**: A descrição é para o leitor humano no catálogo; o teste é para a pipeline — FK sem teste é documentação que pode divergir silenciosamente da realidade.

### 4.3 FKs com NULL excluídas do teste `relationships`

**Decisão**: `seller_id` no intermediate tem `where: "seller_id is not null"` no teste relationships.

**Rationale**: `seller_id` é NULL para pedidos `multi_vendedor = true` (1.278 casos). Sem o `where`, o teste falharia com erro de FK. Documentar o NULL na descrição é suficiente para o leitor.

### 4.4 Conteúdo mínimo por coluna

Toda coluna deve ter:
- `description`: 1 frase de negócio, em português
- Para FKs: prefixo `"FK para <model>.<coluna>. "` + o que representa
- Para métricas calculadas: fórmula abreviada entre parênteses

---

## 5. FKs e Testes `relationships` a Declarar

| Coluna | Model origem | Referência | Filtro |
|---|---|---|---|
| `customer_id` | `olist__orders` | `olist__customers.customer_id` | — |
| `order_id` | `olist__order_items` | `olist__orders.order_id` | — |
| `seller_id` | `olist__order_items` | `olist__sellers.seller_id` | — |
| `order_id` | `olist__order_reviews` | `olist__orders.order_id` | — |
| `customer_id` | `intermediate__pedidos_enriquecidos` | `olist__customers.customer_id` | — |
| `seller_id` | `intermediate__pedidos_enriquecidos` | `olist__sellers.seller_id` | `seller_id is not null` |

---

## 6. Execução

```bash
cd dbt_olist

# Gerar catálogo (manifesto + catalog.json)
dbt docs generate --profiles-dir .

# Servir o catálogo no navegador
dbt docs serve --port 8080 --profiles-dir .
```

---

## 7. Critérios de Aceitação (DoD)

- [ ] `dbt docs generate` conclui sem erros
- [ ] `dbt docs serve` abre o catálogo no navegador (porta 8080)
- [ ] Toda tabela tem `description` preenchida
- [ ] Toda coluna de staging, intermediate e marts tem `description` preenchida
- [ ] Todas as 6 FKs da seção 5 têm teste `relationships` declarado
- [ ] `dbt test` continua com 0 falhas após adicionar os novos testes relationships

---

**Responsável**: Novaes  
**Aprovação**: Pendente
