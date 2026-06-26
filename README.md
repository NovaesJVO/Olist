# Olist Project Skeleton

Projeto base para pipeline de ETL com dbt + PostgreSQL + Python.

## Estrutura

- `docker-compose.yml`
- `.env.example`
- `requirements.txt`
- `README.md`
- `sql/ddl_bronze.sql`
- `ingestion/date_shift_olist.py`
- `ingestion/load_to_postgres.py`
- `dbt/sertao_olist/`
  - `dbt_project.yml`
  - `packages.yml`
  - `profiles.yml.example`
  - `macros/`
  - `models/staging/`
  - `models/intermediate/`
  - `models/marts/`
  - `tests/`
