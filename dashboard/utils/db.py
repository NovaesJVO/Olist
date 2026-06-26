import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine


def _engine():
    host = os.getenv("PG_HOST", "127.0.0.1")
    port = os.getenv("PG_PORT", "5433")
    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "postgres")
    db = os.getenv("PG_DB", "olist")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")


@st.cache_data(ttl=300)
def load_visao_executiva() -> pd.DataFrame:
    with _engine().connect() as conn:
        df = pd.read_sql("SELECT * FROM gold.ecommerce__visao_executiva ORDER BY mes", conn)
    df["mes"] = pd.to_datetime(df["mes"])
    return df


@st.cache_data(ttl=300)
def load_pedidos() -> pd.DataFrame:
    with _engine().connect() as conn:
        df = pd.read_sql("""
            SELECT customer_state, seller_state, multi_vendedor, qtd_itens,
                   valor_produtos, valor_frete, review_score, purchased_at,
                   tempo_aprovacao_dias, tempo_postagem_dias, tempo_transporte_dias,
                   lead_time_total_dias, atraso_entrega_dias, atrasado, nota_baixa
            FROM gold.ecommerce__pedidos
        """, conn)
    df["purchased_at"] = pd.to_datetime(df["purchased_at"], utc=True)
    df["mes"] = df["purchased_at"].dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data(ttl=300)
def load_vendedores() -> pd.DataFrame:
    with _engine().connect() as conn:
        return pd.read_sql(
            "SELECT * FROM gold.ecommerce__vendedores ORDER BY receita_produtos DESC", conn
        )


@st.cache_data(ttl=300)
def load_geografia() -> pd.DataFrame:
    with _engine().connect() as conn:
        return pd.read_sql(
            "SELECT * FROM gold.ecommerce__geografia ORDER BY customer_state", conn
        )


_ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


def sidebar_filters():
    st.sidebar.title("🔍 Filtros")
    meses = pd.date_range("2023-09-01", "2025-08-01", freq="MS")
    labels = [m.strftime("%b/%Y") for m in meses]

    idx_ini, idx_fim = st.sidebar.select_slider(
        "Período",
        options=list(range(len(labels))),
        value=(0, len(labels) - 1),
        format_func=lambda i: labels[i],
    )
    periodo = (meses[idx_ini], meses[idx_fim])

    ufs = st.sidebar.multiselect("UF do Cliente", options=_ALL_UFS, default=_ALL_UFS)
    if not ufs:
        ufs = _ALL_UFS

    return periodo, ufs
