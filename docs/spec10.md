# SPEC 10: Dashboard Streamlit — Consumo dos Marts Gold

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Criar um dashboard web em Streamlit com 5 páginas que consome os 4 marts gold via SQLAlchemy, com filtros globais de período e UF na sidebar.

---

## 2. Contexto

- **Pré-requisito**: SPEC 08 concluída — 4 marts gold validados e disponíveis
- **Filosofia**: Python puro, sem ferramenta de BI externa — mesma stack do pipeline
- **Porta do Postgres**: 5433 (mudada na SPEC 04 para evitar conflito com Postgres nativo do Windows)

---

## 3. Estrutura de Arquivos

```
dashboard/
├── Home.py                      # Visão Executiva (página inicial)
├── pages/
│   ├── 1_Entrega.py             # Entrega ponta a ponta
│   ├── 2_Vendedores.py          # Vendedores críticos
│   ├── 3_Geografia.py           # Atraso e nota por UF
│   └── 4_Arquitetura_Tecnica.py # Descrição técnica do pipeline
└── utils/
    └── db.py                    # Conexão SQLAlchemy + queries cacheadas
```

---

## 4. Decisões Técnicas

### 4.1 Conexão: SQLAlchemy lendo do schema `gold`

**Decisão**: `create_engine()` com as mesmas variáveis de ambiente do pipeline (`PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DB`). Padrão local aponta para `localhost:5433`.

**Rationale**: Sem duplicação de dados. O Postgres já está rodando via Docker — leitura direta é a arquitetura mais simples.

### 4.2 Cache com `@st.cache_data(ttl=300)`

**Decisão**: Todas as queries são cacheadas por 5 minutos.

**Rationale**: Os marts gold são tabelas estáticas (dados do Kaggle). Sem cache, cada interação com filtros bate no banco — desnecessário e lento.

### 4.3 Filtros globais na sidebar

**Decisão**: Dois filtros compartilhados entre páginas via `st.session_state`:
- **Período**: slider de meses (range dentro de set/2023–ago/2025)
- **UF do cliente**: multiselect com todos os 27 estados

**Aplicação por página**:

| Página | Filtro período | Filtro UF |
|---|---|---|
| Home (Visão Executiva) | `mes` em `visao_executiva` | — (série mensal, sem UF) |
| Entrega | `purchased_at` truncado no mês em `pedidos` | `customer_state` em `pedidos` |
| Vendedores | — (agregado, sem data) | `seller_state` em `vendedores` |
| Geografia | — (já é por UF) | destaque visual da UF selecionada |

### 4.4 Gráficos com Plotly Express

**Decisão**: Plotly Express para todos os charts interativos.

**Rationale**: Integração nativa com Streamlit via `st.plotly_chart()`, tooltip interativo e zoom sem dependências externas.

### 4.5 Página de Arquitetura Técnica: sem queries

**Decisão**: Página estática com descrição do pipeline em Markdown + diagrama em texto.

**Rationale**: Demonstra o contexto técnico do projeto para avaliadores sem requerer interação com o banco.

---

## 5. Especificação das Páginas

### 5.1 `Home.py` — Visão Executiva

**Fonte**: `gold.ecommerce__visao_executiva` (filtrado por período)

**KPIs** (linha de métricas no topo):
- Total de pedidos no período
- Receita total de produtos
- % pedidos atrasados
- Nota média de satisfação

**Charts**:
- Linha: pedidos por mês + linha de nota_media (eixo duplo)
- Barras: receita_produtos por mês
- Linha: pct_atrasado por mês (destaque visual quando > 10%)

---

### 5.2 `1_Entrega.py` — Entrega Ponta a Ponta

**Fonte**: `gold.ecommerce__pedidos` (filtrado por período + UF)

**KPIs**:
- Lead time médio (dias)
- % pedidos atrasados
- Atraso médio (dias)
- Etapa mais lenta (aprovação / postagem / transporte)

**Charts**:
- Barras empilhadas: média de tempo por etapa (aprovação + postagem + transporte)
- Histograma: distribuição do lead_time_total_dias
- Scatter: atraso_entrega_dias × review_score (correlação atraso/satisfação)

---

### 5.3 `2_Vendedores.py` — Vendedores Críticos

**Fonte**: `gold.ecommerce__vendedores` (filtrado por UF do vendedor)

**KPIs**:
- Total de vendedores
- Vendedor com maior receita
- Pior % de atraso (mínimo 10 pedidos)
- Menor nota média (mínimo 10 pedidos)

**Charts**:
- Scatter: receita_produtos × pct_atrasado (tamanho = total_pedidos, cor = nota_media)
- Tabela: Top 20 vendedores críticos (alto volume + nota baixa), ordenável
- Barras: distribuição de nota_media por faixa

---

### 5.4 `3_Geografia.py` — Atraso e Nota por UF

**Fonte**: `gold.ecommerce__geografia`

**KPIs**:
- UF com maior atraso médio
- UF com menor nota média
- UF com maior % interestadual
- UF com maior volume

**Charts**:
- Barras horizontais: atraso_medio_dias por UF (ordenado, UF selecionada destacada)
- Barras horizontais: nota_media por UF
- Scatter: pct_interestadual × atraso_medio_dias (tamanho = total_pedidos)

---

### 5.5 `4_Arquitetura_Tecnica.py` — Arquitetura Técnica

**Fonte**: nenhuma (página estática)

**Conteúdo**:
- Diagrama do pipeline em Markdown (bronze → silver → gold)
- Tabela de tecnologias: Python, PostgreSQL, dbt, Streamlit, Plotly
- Links para specs e catálogo de dados no repositório
- Contagens de linhas por camada (hardcoded dos valores validados)

---

## 6. Dependências

Adicionar a `requirements-dashboard.txt` (arquivo novo, separado do pipeline):

```
streamlit>=1.35
plotly>=5.20
sqlalchemy>=2.0
psycopg2-binary>=2.9
pandas>=2.0
python-dotenv>=1.0
```

---

## 7. Execução

```bash
# Postgres deve estar rodando (porta 5433)
docker compose up -d

# Instalar dependências
pip install -r requirements-dashboard.txt

# Rodar o dashboard
streamlit run dashboard/Home.py
```

---

## 8. Critérios de Aceitação (DoD)

- [ ] `streamlit run dashboard/Home.py` abre no navegador sem erro
- [ ] Home exibe KPIs e 3 gráficos com dados reais
- [ ] Página Entrega carrega e filtros de UF/período refletem nos charts
- [ ] Página Vendedores exibe scatter e tabela Top 20
- [ ] Página Geografia exibe barras por UF com destaque
- [ ] Página Arquitetura carrega sem query ao banco
- [ ] Filtro de UF no sidebar filtra Entrega e Vendedores simultaneamente
- [ ] Sem erros no console do Streamlit com Docker rodando

---

**Próxima Revisão**: Após implementação e validação  
**Responsável**: Novaes  
**Aprovação**: Pendente
