#!/usr/bin/env python3
"""
Carrega CSVs de dados_ajustados/ nas tabelas bronze do PostgreSQL.
Estratégia: TRUNCATE + COPY (idempotente).
Metadados _extracted_at e _source adicionados automaticamente por linha.
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg

CSV_TO_TABLE = {
    "olist_orders_dataset.csv":        "bronze.olist__orders",
    "olist_order_items_dataset.csv":   "bronze.olist__order_items",
    "olist_order_reviews_dataset.csv": "bronze.olist__order_reviews",
    "olist_customers_dataset.csv":     "bronze.olist__customers",
    "olist_sellers_dataset.csv":       "bronze.olist__sellers",
}


def load_all(shifted_dir: str, conn_str: str) -> None:
    csv_path = Path(shifted_dir)
    extracted_at = datetime.now(timezone.utc)

    with psycopg.connect(conn_str) as conn:
        for filename, table in CSV_TO_TABLE.items():
            filepath = csv_path / filename
            if not filepath.exists():
                print(f"  ⚠️  {filename} não encontrado, pulando")
                continue

            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {table}")
                with cur.copy(f"COPY {table} FROM STDIN") as copy:
                    with open(filepath, newline="", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        next(reader)  # skip header
                        for row in reader:
                            normalized = [v if v != "" else None for v in row]
                            normalized.extend([extracted_at, filename])
                            copy.write_row(normalized)

            conn.commit()
            rows = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"  ✅ {table}: {rows:,} linhas")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Carga CSV → bronze (PostgreSQL)")
    parser.add_argument("--shifted-dir", default="./dados_ajustados")
    args = parser.parse_args()

    conn_str = (
        f"host={os.getenv('PG_HOST', 'localhost')} "
        f"port={os.getenv('PG_PORT', '5432')} "
        f"dbname={os.getenv('PG_DB', 'olist')} "
        f"user={os.getenv('PG_USER', 'postgres')} "
        f"password={os.getenv('PG_PASSWORD', 'postgres')}"
    )

    load_all(args.shifted_dir, conn_str)
