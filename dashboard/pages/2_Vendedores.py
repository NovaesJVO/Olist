import streamlit as st
import plotly.express as px
from utils.db import load_vendedores, sidebar_filters

st.set_page_config(page_title="Olist | Vendedores", page_icon="🏪", layout="wide")
st.title("🏪 Vendedores Críticos")

df = load_vendedores()
_, ufs = sidebar_filters()

df_f = df[df["seller_state"].isin(ufs)] if ufs else df

if df_f.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

com_volume = df_f[df_f["total_pedidos"] >= 10]
top_receita = df_f.loc[df_f["receita_produtos"].idxmax()]
pior_atraso = com_volume.nlargest(1, "pct_atrasado").iloc[0]
pior_nota = com_volume.nsmallest(1, "nota_media").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vendedores", f"{len(df_f):,}")
c2.metric("Maior receita", f"R$ {top_receita['receita_produtos']:,.0f}")
c3.metric("Pior % atraso (≥10 ped.)", f"{pior_atraso['pct_atrasado']:.1f}%")
c4.metric("Menor nota (≥10 ped.)", f"{pior_nota['nota_media']:.2f} ⭐")

st.divider()

col1, col2 = st.columns([1.3, 0.7])

with col1:
    fig1 = px.scatter(
        df_f, x="receita_produtos", y="pct_atrasado",
        size="total_pedidos", color="nota_media",
        hover_data={"seller_id": True, "seller_state": True, "total_pedidos": True},
        title="Receita × % Atrasados (tamanho = pedidos, cor = nota)",
        labels={"receita_produtos": "Receita (R$)", "pct_atrasado": "% Atrasados"},
        color_continuous_scale="RdYlGn_r",
        size_max=30,
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Top 20 Críticos")
    st.caption("Mínimo 10 pedidos · ordenado por menor nota")
    tabela = (
        com_volume
        .nsmallest(20, "nota_media")
        [["seller_id", "seller_state", "total_pedidos", "nota_media", "pct_atrasado", "receita_produtos"]]
        .assign(
            seller_id=lambda d: d["seller_id"].str[:10] + "…",
            nota_media=lambda d: d["nota_media"].round(2),
            pct_atrasado=lambda d: d["pct_atrasado"].round(1),
            receita_produtos=lambda d: d["receita_produtos"].apply(lambda v: f"R$ {v:,.0f}"),
        )
        .rename(columns={
            "seller_id": "Seller", "seller_state": "UF", "total_pedidos": "Pedidos",
            "nota_media": "Nota", "pct_atrasado": "% Atraso", "receita_produtos": "Receita",
        })
    )
    st.dataframe(tabela, use_container_width=True, hide_index=True)
