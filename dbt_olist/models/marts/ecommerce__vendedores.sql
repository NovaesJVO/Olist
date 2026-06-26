with base as (
    select *
    from {{ ref('intermediate__pedidos_enriquecidos') }}
    where order_status  = 'delivered'
      and multi_vendedor = false
),

agregado as (
    select
        seller_id,
        seller_state,
        count(*)                         as total_pedidos,
        sum(qtd_itens)                   as total_itens,
        sum(valor_produtos)              as receita_produtos,
        sum(valor_frete)                 as receita_frete,
        avg(valor_produtos)              as ticket_medio,
        avg(lead_time_total_dias)        as lead_time_medio_dias,
        avg(atrasado::int)  * 100        as pct_atrasado,
        avg(review_score)                as nota_media,
        avg(nota_baixa::int) * 100       as pct_nota_baixa
    from base
    group by seller_id, seller_state
)

select
    *,
    rank() over (order by receita_produtos desc) as ranking_receita
from agregado
