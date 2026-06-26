# SPEC 01B: Date Shifting - Ajuste de Datas do Dataset Olist

**Versão**: 1.0  
**Data**: 2026-06-26  
**Status**: Especificação Inicial  

---

## 1. Objetivo

Aplicar um offset fixo de **2556 dias** (≈7 anos) em todas as colunas de timestamp do dataset Olist, deslocando datas de 2016-2018 para 2023-2025, preservando exatamente as durações entre datas.

---

## 2. Motivação

- **Dataset Original**: Transações de 2016-2018 (dados históricos, ~2 anos)
- **Problema**: Alguns modelos/análises precisam de dados recentes
- **Solução**: Deslocar datas mantendo os padrões temporais intactos
- **Benefício**: Simula como seria o dataset "hoje" sem distorcer relações temporais

---

## 3. Escopo

### 3.1 O que está incluso

- Identificação de 8 colunas de timestamp em 3 arquivos CSV
- Aplicação de offset fixo (+2556 dias) em todas as colunas
- Preservação de durações e intervalos entre datas
- Geração de pasta `dados_ajustados/` com todos os 9 arquivos (apenas 3 modificados)
- Validação automática: verificar que durações são preservadas
- Documentação do procedimento

### 3.2 O que **não** está incluso

- Correção de dados faltantes ou inválidos
- Mudança de granularidade temporal
- Transformações de negócio (ex.: agregações)

---

## 4. Detalhes Técnicos

### 4.1 Offset Fixo vs. Dinâmico

**Decisão**: Offset fixo de 2556 dias (NÃO varia por arquivo ou período)

**Rationale**:
- Mantém relações temporais intactas
- Simples e reproduzível
- Não distorce pedidos que atravessam fev/mar (évita edge cases de cálculo de ano)
- Período resultante: ~setembro/2023 a outubro/2025

### 4.2 Colunas de Timestamp (8 no total)

#### Arquivo: `olist_orders_dataset.csv` (5 colunas)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `order_purchase_timestamp` | timestamp | Momento do pedido |
| `order_approved_at` | timestamp | Aprovação do pedido |
| `order_delivered_carrier_date` | timestamp | Entrega ao transportador |
| `order_delivered_customer_date` | timestamp | Entrega ao cliente |
| `order_estimated_delivery_date` | timestamp | Data estimada de entrega |

#### Arquivo: `olist_order_items_dataset.csv` (1 coluna)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `shipping_limit_date` | timestamp | Prazo máximo de envio |

#### Arquivo: `olist_order_reviews_dataset.csv` (2 colunas)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `review_creation_date` | timestamp | Data de criação da review |
| `review_answer_timestamp` | timestamp | Data de resposta da review |

**Total**: 5 + 1 + 2 = **8 colunas de timestamp**

### 4.3 Validação de Durações

Para cada par de datas relacionadas, validar que a duração é preservada:

```python
# Exemplo: order_purchase_timestamp vs order_delivered_customer_date
duração_original = df_original['order_delivered_customer_date'] - df_original['order_purchase_timestamp']
duração_ajustada = df_ajustado['order_delivered_customer_date'] - df_ajustado['order_purchase_timestamp']

assert (duração_original == duração_ajustada).all(), "Durações não coincidem!"
```

---

## 5. Especificação do Script

### 5.1 Entrada

```bash
python ingestion/date_shift_olist.py \
  --input-dir ./dados_originais \
  --output-dir ./dados_ajustados
```

### 5.2 Lógica

```python
import pandas as pd
from datetime import timedelta
from pathlib import Path

def shift_dates(input_dir, output_dir, offset_days=2556):
    """Aplica offset fixo em colunas de timestamp."""
    
    offset = timedelta(days=offset_days)
    timestamp_cols = {
        'olist_orders_dataset.csv': [
            'order_purchase_timestamp',
            'order_approved_at',
            'order_delivered_carrier_date',
            'order_delivered_customer_date',
            'order_estimated_delivery_date'
        ],
        'olist_order_items_dataset.csv': [
            'shipping_limit_date'
        ],
        'olist_order_reviews_dataset.csv': [
            'review_creation_date',
            'review_answer_timestamp'
        ]
    }
    
    Path(output_dir).mkdir(exist_ok=True)
    
    # Copia todos os 9 arquivos
    for csv_file in Path(input_dir).glob('*.csv'):
        output_file = Path(output_dir) / csv_file.name
        
        # Se não tem colunas de timestamp, apenas copia
        if csv_file.name not in timestamp_cols:
            df.to_csv(output_file, index=False)
            continue
        
        # Lê CSV e converte colunas para datetime
        df = pd.read_csv(csv_file)
        cols_to_shift = timestamp_cols[csv_file.name]
        
        for col in cols_to_shift:
            df[col] = pd.to_datetime(df[col]) + offset
        
        # Salva com datas ajustadas
        df.to_csv(output_file, index=False)
    
    return True
```

### 5.3 Saída

```
dados_ajustados/
├── olist_customers_dataset.csv (cópia idêntica)
├── olist_geolocation_dataset.csv (cópia idêntica)
├── olist_order_items_dataset.csv (1 col ajustada: shipping_limit_date)
├── olist_order_payments_dataset.csv (cópia idêntica)
├── olist_order_reviews_dataset.csv (2 cols ajustadas: review_creation_date, review_answer_timestamp)
├── olist_orders_dataset.csv (5 cols ajustadas)
├── olist_products_dataset.csv (cópia idêntica)
├── olist_sellers_dataset.csv (cópia idêntica)
└── product_category_name_translation.csv (cópia idêntica)
```

---

## 6. Critérios de Aceitação (DoD)

- [x] Script `ingestion/date_shift_olist.py` implementado e testado
- [x] Pasta `dados_ajustados/` criada com 9 arquivos
- [x] 8 colunas de timestamp ajustadas com offset de 2556 dias
- [x] Validação: durações entre datas são idênticas (diferença = 0.00s)
- [x] Período resultante: ~setembro/2023 a outubro/2025
- [x] Comando executa sem erros:
  ```bash
  python ingestion/date_shift_olist.py --input-dir ./dados_originais --output-dir ./dados_ajustados
  ```
- [x] Relatório de validação impresso ao final
- [x] `.gitignore` inclui `dados_ajustados/` (dados não versionam)
- [x] Documentação atualizada

**Status**: ✅ **CONCLUÍDO** - 2026-06-26
- Script validado com sucesso
- Todos os 9 arquivos criados
- Durações preservadas (Diff = 0.00s)

---

## 7. Referência de Datas

| Período | Data (Amostra) |
|---------|---|
| **Original** | 2016-09-04 a 2018-10-17 |
| **Ajustado (+ 2556 dias)** | 2023-09-04 a 2025-10-17 |

---

## 8. Notas

- Offset fixo garante que durações são preservadas exatamente
- Não há problema com anos bissextos (offset é dia exato)
- NULLs em colunas de timestamp são preservados
- Demais dados (valores, IDs, categorias) permanecem intactos

---

**Próxima Revisão**: Após implementação e validação  
**Responsável**: Novaes  
