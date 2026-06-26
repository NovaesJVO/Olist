import streamlit as st
import plotly.express as px
from utils.db import load_pedidos, sidebar_filters

st.set_page_config(page_title="Olist | Entrega", page_icon="🚚", layout="wide")
st.title("🚚 Entrega Ponta a Ponta")

df = load_pedidos()
periodo, ufs = sidebar_filters()

mask = (
    (df["mes"] >= periodo[0]) &
    (df["mes"] <= periodo[1]) &
    (df["customer_state"].isin(ufs))
)
df_f = df[mask]

if df_f.empty:
    st.warning("Nenhum dado com os filtros selecionados.")
    st.stop()

etapas = df_f[["tempo_aprovacao_dias", "tempo_postagem_dias", "tempo_transporte_dias"]].mean()
nomes = {"tempo_aprovacao_dias": "Aprovação", "tempo_postagem_dias": "Postagem", "tempo_transporte_dias": "Transporte"}
mais_lenta = nomes[etapas.idxmax()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lead time médio", f"{df_f['lead_time_total_dias'].mean():.1f} dias")
c2.metric("% Atrasados", f"{df_f['atrasado'].mean() * 100:.1f}%")
c3.metric("Atraso médio", f"{df_f['atraso_entrega_dias'].mean():.1f} dias")
c4.metric("Etapa mais lenta", mais_lenta, f"{etapas.max():.1f} dias")

st.divider()

fig1 = px.bar(
    x=list(nomes.values()), y=[etapas[k] for k in nomes],
    title="Tempo Médio por Etapa do Fulfillment (dias)",
    labels={"x": "Etapa", "y": "Dias"},
    color=list(nomes.values()),
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    fig2 = px.histogram(
        df_f, x="lead_time_total_dias", nbins=40,
        title="Distribuição do Lead Time Total (dias)",
        labels={"lead_time_total_dias": "Dias"},
        color_discrete_sequence=["#4C78A8"],
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    sample = (
        df_f.dropna(subset=["atraso_entrega_dias", "review_score"])
        .sample(min(5000, len(df_f)), random_state=42)
    )
    fig3 = px.scatter(
        sample, x="atraso_entrega_dias", y="review_score",
        title="Atraso × Nota do Cliente (amostra)",
        labels={"atraso_entrega_dias": "Dias de atraso (+= atrasado)", "review_score": "Nota"},
        opacity=0.3, color_discrete_sequence=["#F58518"],
    )
    fig3.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="no prazo")
    st.plotly_chart(fig3, use_container_width=True)
