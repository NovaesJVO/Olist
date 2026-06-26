#!/usr/bin/env python3
"""
Pipeline de inicialização Olist.

Passos: unzip → date_shift → DDL → load
Executado pelo serviço `pipeline` do docker-compose.
"""

import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import psycopg
from date_shift_olist import shift_dates
from load_to_postgres import load_all

BASE            = Path(__file__).parent.parent
ARCHIVE         = BASE / "archive.zip"
DADOS_ORIGINAIS = BASE / "dados_originais"
DADOS_AJUSTADOS = BASE / "dados_ajustados"
DDL_PATH        = BASE / "sql" / "ddl_bronze.sql"

CONN_STR = (
    f"host={os.getenv('PG_HOST', 'localhost')} "
    f"port={os.getenv('PG_PORT', '5432')} "
    f"dbname={os.getenv('PG_DB', 'olist')} "
    f"user={os.getenv('PG_USER', 'postgres')} "
    f"password={os.getenv('PG_PASSWORD', 'postgres')}"
)


def step_unzip():
    print("\n[1/4] Descompactando archive.zip...")
    if not ARCHIVE.exists():
        print(f"  ❌ {ARCHIVE} não encontrado")
        sys.exit(1)
    DADOS_ORIGINAIS.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as zf:
        zf.extractall(DADOS_ORIGINAIS)
    count = len(list(DADOS_ORIGINAIS.glob("*.csv")))
    print(f"  ✅ {count} CSVs extraídos → {DADOS_ORIGINAIS}")


def step_date_shift():
    print("\n[2/4] Aplicando date shift (+2556 dias)...")
    result = shift_dates(str(DADOS_ORIGINAIS), str(DADOS_AJUSTADOS))
    if result is None:
        print("  ❌ Date shift falhou")
        sys.exit(1)
    print("  ✅ Date shift concluído")


def step_ddl():
    print("\n[3/4] Criando schemas e tabelas...")
    ddl = DDL_PATH.read_text()
    stmts = [s.strip() for s in ddl.split(";") if s.strip()]
    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            for stmt in stmts:
                cur.execute(stmt)
        conn.commit()
    print("  ✅ DDL aplicado (schemas bronze/silver/gold + 5 tabelas)")


def step_load():
    print("\n[4/4] Carregando CSVs nas tabelas bronze...")
    load_all(str(DADOS_AJUSTADOS), CONN_STR)


def main():
    print("=" * 50)
    print("  PIPELINE OLIST — INICIALIZAÇÃO")
    print("=" * 50)
    step_unzip()
    step_date_shift()
    step_ddl()
    step_load()
    print("\n" + "=" * 50)
    print("  PIPELINE CONCLUÍDO ✅")
    print("=" * 50)


if __name__ == "__main__":
    main()
