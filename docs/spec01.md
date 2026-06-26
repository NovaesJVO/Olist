# SPEC 01: Ingestão de Dados Originais do Brazilian E-Commerce Olist

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Obter os 9 CSVs originais do dataset público de E-Commerce brasileiro (Olist) e organizá-los em uma pasta estruturada (`dados_originais/`) como primeiro artefato de dados brutos do pipeline.

---

## 2. Contexto e Motivação

- **Fonte de Dados**: Brazilian E-Commerce Public Dataset by Olist (Kaggle)
  - URL: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
  - Acesso: Público (requer login no Kaggle)
  - Tamanho aproximado: ~100 MB (descompactado)

- **Objetivo do Pipeline**: Estruturar um ELT robusto com dbt + PostgreSQL + Python
  - Extract: Python (download dos CSVs)
  - Load: Python (ingesta no PostgreSQL)
  - Transform: dbt (modelagem em camadas: bronze → silver → gold)

- **Por que este dataset?**
  - Dataset real e completo de transações de e-commerce
  - Contém múltiplas entidades relacionadas (pedidos, clientes, produtos, pagamentos, etc.)
  - Adequado para demonstrar modelagem dimensional e análises comerciais
  - Acesso livre e reproduzível

---

## 3. Escopo

### 3.1 O que está incluso

- Download dos 9 arquivos CSV originais do Kaggle
- Armazenamento local em pasta dedicada (`dados_originais/`)
- Validação básica de integridade (contagem de linhas, tamanho)
- Registro de metadados dos arquivos
- Documentação da estrutura

### 3.2 O que **não** está incluso

- Processamento ou transformação dos dados
- Criação de tabelas no PostgreSQL (será feito na próxima etapa)
- Análises exploratórias
- Data quality ou data profiling detalhado

---

## 4. Requisitos Funcionais

### 4.1 Arquivos Esperados

Os seguintes 9 arquivos devem ser baixados do Kaggle:

| # | Arquivo | Descrição | Registros Esperados |
|---|---------|-----------|-------------------|
| 1 | `olist_customers_dataset.csv` | Dados de clientes | ~100 K |
| 2 | `olist_geolocation_dataset.csv` | Tabela de geolocalização (CEP → coordenadas) | ~1 M |
| 3 | `olist_order_items_dataset.csv` | Itens dentro de pedidos | ~112 K |
| 4 | `olist_order_payments_dataset.csv` | Métodos e parcelas de pagamento | ~113 K |
| 5 | `olist_order_reviews_dataset.csv` | Reviews/avaliações de pedidos | ~99 K |
| 6 | `olist_orders_dataset.csv` | Cabeçalho dos pedidos | ~99 K |
| 7 | `olist_products_dataset.csv` | Catálogo de produtos | ~32 K |
| 8 | `olist_sellers_dataset.csv` | Dados dos vendedores | ~3 K |
| 9 | `product_category_name_translation.csv` | Tradução de categorias (PT → EN) | ~71 |

### 4.2 Estrutura de Armazenamento

```
Olist/
├── dados_originais/
│   ├── olist_customers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── product_category_name_translation.csv
```

### 4.3 Requisitos Técnicos

- Os arquivos devem estar em formato CSV UTF-8
- Os nomes de arquivo **não devem ser alterados** (manter nomes originais do Kaggle)
- Não deve haver descompactação ou conversão de formato
- Pasta deve estar em `.gitignore` (dados brutos não versionam com código)

---

## 5. Decisões Técnicas

### 5.1 Fonte e Autenticação

**Decisão**: Usar Kaggle API via CLI ou Python SDK

**Rationale**:
- Acesso automatizado e reproduzível
- Não requer clicks manuais
- Suporta versionamento e CI/CD futuro

**Pré-requisitos**:
- Biblioteca Python `kaggle` instalada
- Arquivo `~/.kaggle/kaggle.json` com credenciais da API

### 5.2 Nomes de Arquivo

**Decisão**: Preservar nomes originais do Kaggle

**Rationale**:
- Mantém rastreabilidade e corresponde à documentação oficial
- Facilita reconciliação com versões futuras
- Evita renomeações desnecessárias

### 5.3 Versionamento Git

**Decisão**: Adicionar `dados_originais/` ao `.gitignore`

**Rationale**:
- CSVs originais são grandes (~100 MB)
- Dados brutos devem ser obtidos de fonte confiável, não versionados
- Reproduzibilidade via script de download, não via git

---

## 6. Critérios de Aceitação (DoD)

- [x] Pasta `dados_originais/` existe no root do projeto
- [x] Todos os 9 arquivos CSV estão presentes com nomes originais
- [x] Contagem aproximada de linhas:
  - `olist_customers_dataset.csv` ≈ 100 K linhas
  - `olist_orders_dataset.csv` ≈ 99 K linhas (referência principal)
  - `olist_geolocation_dataset.csv` ≈ 1 M linhas
  - Demais arquivos com linha apropriados
- [x] Arquivo `dados_originais/.gitkeep` ou entrada em `.gitignore` confirmada
- [x] Comando `ls dados_originais/` ou `dir dados_originais/` lista os 9 arquivos
- [x] Nenhum erro de encoding ou corrupção detectado
- [x] Esta spec e script de download documentados em `docs/`

**Status**: ✅ **CONCLUÍDO** - Dataset extraído em 2026-06-26

---

## 7. Próximas Etapas

### 7.1 Etapa Imediata (Spec 02)

- **DDL Bronze**: Criar tabelas no PostgreSQL correspondentes aos 9 CSVs
- Script SQL: `sql/ddl_bronze.sql`
- Deve incluir constraints, tipos de dados apropriados
- Sem índices ou keys externas (apenas raw data)

### 7.2 Etapa Seguinte (Spec 03)

- **Ingestão de Dados**: Python scripts para carregar CSVs → PostgreSQL
- `ingestion/load_to_postgres.py`
- Tratamento de erros e logging
- Validação pós-carga (row counts, nulls)

### 7.3 Longo Prazo

- Modelagem dbt (staging → marts)
- Data quality checks
- CI/CD pipeline
- Documentação de dados (data dictionary)

---

## 8. Implementação

### 8.1 Método de Ingestão

**Opção 1 (Automatizado - Não Utilizada)**:
```python
import kaggle
from pathlib import Path

output_dir = Path("dados_originais")
output_dir.mkdir(exist_ok=True)
dataset = "olistbr/brazilian-ecommerce"
kaggle.api.dataset_download_files(dataset, path=output_dir, unzip=True)
```

**Opção 2 (Utilizada) - Download Manual via Kaggle Web**:
1. Acessar https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Clicar "Download"
3. Extrair `archive.zip` para `dados_originais/`
4. Verificar: 9 arquivos CSV presentes

**Status Atual**: ✅ **CONCLUÍDO** (2026-06-26)
- 9 arquivos CSV extraídos
- Nomes originais preservados
- Pronto para próxima fase (DDL Bronze)

### 8.2 Inclusão em `.gitignore`

```
# Dados brutos (não versionam)
dados_originais/
```

---

## 9. Referências

- [Kaggle Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Kaggle API Docs](https://github.com/Kaggle/kaggle-api)
- [dbt Documentation](https://docs.getdbt.com/)

---

## 10. Notas e Observações

- O dataset contém transações de 2016–2018 (~2 anos de dados históricos)
- Algumas colunas têm valores NULL; será importante documentar isso na fase DDL
- Relacionamentos entre tabelas devem ser validados antes da modelagem dbt
- Considerar particionamento por data em etapas futuras (incremental loads)

---

**Próxima Revisão**: Após implementação e validação  
**Responsável**: Novaes  
**Aprovação**: Pendente
