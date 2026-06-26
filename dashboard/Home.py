import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import load_visao_executiva, sidebar_filters

st.set_page_config(page_title="Olist | Visão Executiva", page_icon="📦", layout="wide")
st.title("📦 Olist E-Commerce — Visão Executiva")

df = load_visao_executiva()
periodo, _ = sidebar_filters()

mask = (df["mes"] >= periodo[0]) & (df["mes"] <= periodo[1])
df_f = df[mask]

if df_f.empty:
    st.warning("Nenhum dado no período selecionado.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pedidos entregues", f"{int(df_f['total_pedidos'].sum()):,}")
c2.metric("Receita produtos", f"R$ {df_f['receita_produtos'].sum():,.0f}")
c3.metric("% Atrasados", f"{df_f['pct_atrasado'].mean():.1f}%")
c4.metric("Nota média", f"{df_f['nota_media'].mean():.2f} ⭐")

st.divider()

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=df_f["mes"], y=df_f["total_pedidos"],
    name="Pedidos", marker_color="#4C78A8",
))
fig1.add_trace(go.Scatter(
    x=df_f["mes"], y=df_f["nota_media"],
    name="Nota média", yaxis="y2",
    line=dict(color="#F58518", width=2), mode="lines+markers",
))
fig1.update_layout(
    title="Pedidos por Mês e Nota Média de Satisfação",
    yaxis=dict(title="Pedidos entregues"),
    yaxis2=dict(title="Nota (1–5)", overlaying="y", side="right", range=[3, 5]),
    legend=dict(orientation="h", y=1.1),
    height=420,
)
st.plotly_chart(fig1, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    fig2 = px.bar(
        df_f, x="mes", y="receita_produtos",
        title="Receita de Produtos por Mês (R$)",
        labels={"mes": "", "receita_produtos": "R$"},
        color_discrete_sequence=["#54A24B"],
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    fig3 = px.line(
        df_f, x="mes", y="pct_atrasado",
        title="% Pedidos Atrasados por Mês",
        labels={"mes": "", "pct_atrasado": "% Atrasados"},
        markers=True, color_discrete_sequence=["#E45756"],
    )
    fig3.add_hline(y=10, line_dash="dash", line_color="gray", annotation_text="10% referência")
    st.plotly_chart(fig3, use_container_width=True)
