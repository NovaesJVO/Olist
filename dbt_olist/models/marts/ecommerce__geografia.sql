select
    customer_state,
    count(*)                                                                as total_pedidos,
    avg(
        case
            when seller_state is not null
             and seller_state is distinct from customer_state
            then 1 else 0
        end
    ) * 100                                                                 as pct_interestadual,
    avg(lead_time_total_dias)                                               as lead_time_medio_dias,
    avg(atraso_entrega_dias)                                                as atraso_medio_dias,
    avg(atrasado::int) * 100                                                as pct_atrasado,
    avg(review_score)                                                       as nota_media,
    avg(nota_baixa::int) * 100                                              as pct_nota_baixa,
    sum(valor_produtos + valor_frete)                                       as receita_total
from {{ ref('intermediate__pedidos_enriquecidos') }}
where order_status = 'delivered'
group by customer_state
