#!/usr/bin/env python3
"""
Carrega CSVs de dados_ajustados/ nas tabelas bronze do PostgreSQL.
Usa COPY para bulk insert eficiente. Idempotente via TRUNCATE antes de cada carga.
"""

import sys
from pathlib import Path
import psycopg

CSV_TO_TABLE = {
    "olist_orders_dataset.csv":        "bronze.olist__orders",
    "olist_order_items_dataset.csv":   "bronze.olist__order_items",
    "olist_order_reviews_dataset.csv": "bronze.olist__order_reviews",
    "olist_customers_dataset.csv":     "bronze.olist__customers",
    "olist_sellers_dataset.csv":       "bronze.olist__sellers",
}


def load_all(csv_dir: str, conn_str: str) -> None:
    csv_path = Path(csv_dir)
    with psycopg.connect(conn_str) as conn:
        for filename, table in CSV_TO_TABLE.items():
            filepath = csv_path / filename
            if not filepath.exists():
                print(f"  ⚠️  {filename} não encontrado, pulando")
                continue

            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {table}")
                with cur.copy(
                    f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER true, NULL '')"
                ) as copy:
                    with open(filepath, "r", encoding="utf-8") as f:
                        while chunk := f.read(65536):
                            copy.write(chunk)

            conn.commit()
            rows = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"  ✅ {table}: {rows:,} linhas")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Carga CSV → bronze (PostgreSQL)")
    parser.add_argument("--csv-dir", default="./dados_ajustados")
    args = parser.parse_args()

    conn_str = (
        f"host={os.getenv('PG_HOST', 'localhost')} "
        f"port={os.getenv('PG_PORT', '5432')} "
        f"dbname={os.getenv('PG_DB', 'olist')} "
        f"user={os.getenv('PG_USER', 'postgres')} "
        f"password={os.getenv('PG_PASSWORD', 'postgres')}"
    )

    load_all(args.csv_dir, conn_str)
