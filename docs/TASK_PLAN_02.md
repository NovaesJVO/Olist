# TASK PLAN: Implementação de SPEC 02 - DDL Bronze

**Data**: 2026-06-26  
**Branch**: `spec/02-ddl-bronze`  
**Status**: Em andamento  

---

## Objetivo

Executar a especificação SPEC 02: criar os schemas `bronze`, `silver`, `gold` e as 5 tabelas bronze tipadas no PostgreSQL via `sql/ddl_bronze.sql`.

---

## Pré-Requisitos

- [x] **SPEC 01**: `dados_originais/` com 9 CSVs disponíveis
- [x] **SPEC 01B**: `dados_ajustados/` com timestamps deslocados (+2556 dias)
- [x] **DDL escrito**: `sql/ddl_bronze.sql` implementado
- [x] **Spec documentada**: `docs/spec02.md` criada
- [ ] **PostgreSQL rodando**: `docker compose up -d` executado

---

## Tarefas

### Fase 1: Infraestrutura

| # | Tarefa | Status | Notas |
|---|--------|--------|-------|
| 1.1 | Subir container Postgres | [ ] | `docker compose up -d` |
| 1.2 | Confirmar conexão | [ ] | `psql -h localhost -U postgres -d olist -c "\conninfo"` |

### Fase 2: Execução do DDL

| # | Tarefa | Status | Notas |
|---|--------|--------|-------|
| 2.1 | Executar `sql/ddl_bronze.sql` | [ ] | Via psql ou docker exec |
| 2.2 | Verificar schemas criados (`\dn`) | [ ] | Deve listar bronze, silver, gold |
| 2.3 | Verificar tabelas criadas (`\dt bronze.*`) | [ ] | Deve listar 5 tabelas |
| 2.4 | Confirmar tabelas vazias | [ ] | `SELECT count(*) FROM bronze.olist__orders` = 0 |

### Fase 3: Validação de Tipos

| # | Tarefa | Status | Notas |
|---|--------|--------|-------|
| 3.1 | Conferir TIMESTAMPTZ em timestamps | [ ] | `\d bronze.olist__orders` |
| 3.2 | Conferir NUMERIC(12,2) em price/freight | [ ] | `\d bronze.olist__order_items` |
| 3.3 | Conferir CHAR(2) em customer_state e seller_state | [ ] | `\d bronze.olist__customers` |
| 3.4 | Confirmar idempotência: re-executar DDL sem erros | [ ] | Segunda execução deve retornar NOTICE, não ERROR |

### Fase 4: Documentação e Commit

| # | Tarefa | Status | Notas |
|---|--------|--------|-------|
| 4.1 | Marcar DoD no `docs/spec02.md` | [ ] | Atualizar checkboxes |
| 4.2 | Atualizar `docs/TASK_PLAN.md` (Fase 5 da SPEC 01) | [ ] | Marcar 5.1 e 5.2 como concluídos |
| 4.3 | Commit dos artefatos | [ ] | DDL + spec02 + task plan |
| 4.4 | Remover `sql/ddl_bronze copy.sql` | [ ] | Arquivo duplicado |

---

## Comandos de Execução

### Subir Postgres

```bash
docker compose up -d
```

### Executar DDL

```bash
# Opção 1: psql local
psql -h localhost -U postgres -d olist -f sql/ddl_bronze.sql

# Opção 2: via docker exec
docker exec -i $(docker compose ps -q postgres) \
  psql -U postgres -d olist < sql/ddl_bronze.sql
```

### Validar Critérios de Aceitação

```bash
psql -h localhost -U postgres -d olist -c "\dn"
psql -h localhost -U postgres -d olist -c "\dt bronze.*"
psql -h localhost -U postgres -d olist \
  -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'bronze' ORDER BY tablename;"
```

---

## Critérios de Aceitação (DoD)

- [ ] `\dn` lista `bronze`, `silver`, `gold`
- [ ] `\dt bronze.*` lista exatamente 5 tabelas:
  - `bronze.olist__orders`
  - `bronze.olist__order_items`
  - `bronze.olist__order_reviews`
  - `bronze.olist__customers`
  - `bronze.olist__sellers`
- [ ] Todas as tabelas estão **vazias**
- [ ] DDL é idempotente (segunda execução sem erros)
- [ ] Tipos corretos: `TIMESTAMPTZ`, `NUMERIC(12,2)`, `CHAR(2)`

---

## Artefatos

| Artefato | Caminho | Status |
|----------|---------|--------|
| Spec | `docs/spec02.md` | ✅ Criado |
| DDL | `sql/ddl_bronze.sql` | ✅ Implementado |
| Task Plan | `docs/TASK_PLAN_02.md` | ✅ Este arquivo |
| Docker Compose | `docker-compose.yml` | ✅ Existente |

---

## Próximos Passos

- **SPEC 03**: Ingestão ETL — `ingestion/load_to_postgres.py` carrega `dados_ajustados/` nas tabelas bronze

---

## Histórico de Atualizações

| Data | Versão | Mudança |
|------|--------|---------|
| 2026-06-26 | 1.0 | Criação do task plan |
