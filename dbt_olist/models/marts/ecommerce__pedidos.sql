select
    order_id,
    customer_id,
    customer_unique_id,
    customer_state,
    seller_id,
    seller_state,
    multi_vendedor,
    qtd_itens,
    valor_produtos,
    valor_frete,
    review_score,
    purchased_at,
    customer_delivered_at,
    tempo_aprovacao_dias,
    tempo_postagem_dias,
    tempo_transporte_dias,
    lead_time_total_dias,
    atraso_entrega_dias,
    atrasado,
    nota_baixa
from {{ ref('intermediate__pedidos_enriquecidos') }}
where order_status = 'delivered'
