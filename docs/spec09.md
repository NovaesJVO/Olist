# SPEC 09: Catálogo de Dados — Silver e Gold

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Documentar todas as entidades das camadas silver e gold num catálogo de dados estruturado em YAML, cobrindo descrição, linhagem, colunas e ownership — fechando o ciclo de maturidade do pipeline.

---

## 2. Contexto

- **Pré-requisito**: SPEC 08 concluída — pipeline E2E validado
- **Escopo**: 6 entidades silver + 4 entidades gold = 10 arquivos
- **Não cobre**: bronze (dados brutos sem contratos de negócio)

---

## 3. Estrutura de Arquivos

```
catalog/
├── silver/
│   ├── olist__orders.yml
│   ├── olist__order_items.yml
│   ├── olist__order_reviews.yml
│   ├── olist__customers.yml
│   ├── olist__sellers.yml
│   └── intermediate__pedidos_enriquecidos.yml
└── gold/
    ├── ecommerce__pedidos.yml
    ├── ecommerce__vendedores.yml
    ├── ecommerce__geografia.yml
    └── ecommerce__visao_executiva.yml
```

---

## 4. Schema do Catálogo

```yaml
name: <nome_do_model>
layer: silver | gold
domain: olist | ecommerce
description: <descrição em português>
owner: Novaes
lineage:
  sources:
    - <schema.tabela>
  depends_on:
    - <ref dbt>
columns:
  - name: <coluna>
    type: <tipo SQL>
    description: <descrição>
    tests: [unique, not_null]   # apenas quando aplicável
```

---

## 5. Critérios de Aceitação (DoD)

- [ ] 10 arquivos YAML criados em `catalog/silver/` e `catalog/gold/`
- [ ] Todos os campos obrigatórios preenchidos: `name`, `layer`, `domain`, `description`, `owner`, `lineage`, `columns`
- [ ] Colunas conferem com os models SQL (sem colunas `_extracted_at`/`_source` nas entidades silver/gold)
- [ ] Linhagem rastreável de bronze → silver → gold

---

**Responsável**: Novaes
