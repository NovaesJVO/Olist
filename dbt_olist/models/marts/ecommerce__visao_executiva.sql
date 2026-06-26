select
    date_trunc('month', purchased_at)::date  as mes,
    count(*)                                 as total_pedidos,
    sum(valor_produtos)                      as receita_produtos,
    sum(valor_frete)                         as receita_frete,
    avg(valor_produtos)                      as ticket_medio,
    avg(lead_time_total_dias)                as lead_time_medio_dias,
    avg(atrasado::int)  * 100                as pct_atrasado,
    avg(review_score)                        as nota_media,
    avg(nota_baixa::int) * 100               as pct_nota_baixa
from {{ ref('intermediate__pedidos_enriquecidos') }}
where order_status = 'delivered'
group by 1
order by 1
