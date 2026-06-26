import streamlit as st

st.set_page_config(page_title="Olist | Arquitetura", page_icon="⚙️", layout="wide")
st.title("⚙️ Arquitetura Técnica do Pipeline")

st.markdown("""
## Fluxo Completo

```
archive.zip  (Kaggle — dataset estático, transações 2016-2018 → deslocado para 2023-2025)
     │
     ▼  docker compose up --build
 ┌──────────────────────────────────────────┐
 │              INGESTÃO  (Python)           │
 │  1. Unzip  → dados_originais/ (9 CSVs)   │
 │  2. Date shift +2556 dias (3 arquivos)    │
 │  3. DDL: schemas bronze / silver / gold   │
 │  4. COPY CSV → bronze.*  (413.851 linhas) │
 └──────────────────────────────────────────┘
     │
     ▼  dbt build
 ┌──────────────────────────────────────────┐
 │          TRANSFORMAÇÃO  (dbt 1.12)        │
 │  staging      5 views  silver.*           │
 │  intermediate 1 view   silver.*           │
 │  marts        4 tables gold.*             │
 │  tests        33 testes · 0 falhas        │
 └──────────────────────────────────────────┘
     │
     ▼  streamlit run dashboard/Home.py
 ┌──────────────────────────────────────────┐
 │         VISUALIZAÇÃO  (Streamlit)         │
 │  Home     Visão Executiva                 │
 │  Entrega  Lead time e atraso              │
 │  Vendedores  Ranking e críticos           │
 │  Geografia   Atraso e nota por UF         │
 └──────────────────────────────────────────┘
```

---

## Tecnologias

| Camada | Tecnologia | Versão |
|---|---|---|
| Armazenamento | PostgreSQL | 15 (Docker) |
| Orquestração | Docker Compose | 3.9 |
| Ingestão | Python + psycopg3 + pandas | 3.11 |
| Transformação | dbt-core + dbt-postgres | 1.12 |
| Visualização | Streamlit + Plotly | ≥1.35 / ≥5.20 |
| Consultas | SQLAlchemy + psycopg2 | ≥2.0 |

---

## Contagens por Camada

| Camada | Objetos | Linhas |
|---|---|---|
| Bronze | 5 tabelas | 413.851 |
| Silver — staging | 5 views | 413.851 |
| Silver — intermediate | 1 view | 99.441 (grão = pedido) |
| Gold — pedidos | 1 tabela | 96.478 (apenas `delivered`) |
| Gold — vendedores | 1 tabela | 2.948 sellers |
| Gold — geografia | 1 tabela | 27 UFs |
| Gold — visão executiva | 1 tabela | 23 meses (set/2023–ago/2025) |

---

## Estrutura do Repositório

```
Olist/
├── docker-compose.yml          # Postgres 15 (porta 5433) + pipeline
├── Dockerfile                  # Imagem Python para ingestão
├── ingestion/
│   ├── pipeline.py             # Orquestrador: unzip → shift → DDL → COPY
│   ├── date_shift_olist.py     # Date shift +2556 dias
│   └── load_to_postgres.py     # COPY CSV → bronze com metadados
├── sql/ddl_bronze.sql          # Schemas + 5 tabelas tipadas
├── dbt_olist/
│   ├── models/staging/         # 5 views staging
│   ├── models/intermediate/    # 1 model com joins e métricas
│   ├── models/marts/           # 4 marts gold
│   └── tests/                  # Teste singular de sanity check
├── catalog/
│   ├── silver/                 # 6 YAMLs de catálogo
│   └── gold/                   # 4 YAMLs de catálogo
├── dashboard/
│   ├── Home.py                 # Visão Executiva
│   ├── pages/                  # 4 páginas adicionais
│   └── utils/db.py             # Conexão e queries cacheadas
└── docs/
    └── spec01.md → spec10.md   # Especificações de cada etapa
```
""")
