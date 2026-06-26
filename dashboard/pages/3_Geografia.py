import streamlit as st
import plotly.express as px
from utils.db import load_geografia, sidebar_filters

st.set_page_config(page_title="Olist | Geografia", page_icon="🗺️", layout="wide")
st.title("🗺️ Atraso e Satisfação por Estado")

df = load_geografia()
_, ufs = sidebar_filters()

pior_atraso = df.nlargest(1, "atraso_medio_dias").iloc[0]
menor_nota = df.nsmallest(1, "nota_media").iloc[0]
mais_interestadual = df.nlargest(1, "pct_interestadual").iloc[0]
maior_vol = df.nlargest(1, "total_pedidos").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("UF maior atraso", pior_atraso["customer_state"], f"{pior_atraso['atraso_medio_dias']:.1f} dias")
c2.metric("UF menor nota", menor_nota["customer_state"], f"{menor_nota['nota_media']:.2f} ⭐")
c3.metric("UF mais interestadual", mais_interestadual["customer_state"], f"{mais_interestadual['pct_interestadual']:.1f}%")
c4.metric("UF maior volume", maior_vol["customer_state"], f"{int(maior_vol['total_pedidos']):,} ped.")

st.divider()

df["destaque"] = df["customer_state"].isin(ufs)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        df.sort_values("atraso_medio_dias"),
        x="atraso_medio_dias", y="customer_state", orientation="h",
        title="Atraso Médio de Entrega por UF (dias)",
        labels={"atraso_medio_dias": "Dias de atraso", "customer_state": "UF"},
        color="destaque",
        color_discrete_map={True: "#E45756", False: "#9ecae1"},
    )
    fig1.update_layout(showlegend=False, height=620)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(
        df.sort_values("nota_media"),
        x="nota_media", y="customer_state", orientation="h",
        title="Nota Média de Satisfação por UF",
        labels={"nota_media": "Nota média", "customer_state": "UF"},
        color="destaque",
        color_discrete_map={True: "#E45756", False: "#9ecae1"},
    )
    fig2.add_vline(x=4.0, line_dash="dash", line_color="gray", annotation_text="4.0")
    fig2.update_layout(showlegend=False, height=620)
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.scatter(
    df, x="pct_interestadual", y="atraso_medio_dias",
    size="total_pedidos", text="customer_state",
    title="% Interestadual × Atraso Médio (tamanho = volume de pedidos)",
    labels={"pct_interestadual": "% Pedidos interestaduais", "atraso_medio_dias": "Atraso médio (dias)"},
    color="destaque",
    color_discrete_map={True: "#E45756", False: "#4C78A8"},
)
fig3.update_traces(textposition="top center")
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)
