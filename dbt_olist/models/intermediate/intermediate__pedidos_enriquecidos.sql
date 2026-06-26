with orders as (
    select * from {{ ref('olist__orders') }}
),

customers as (
    select * from {{ ref('olist__customers') }}
),

sellers as (
    select * from {{ ref('olist__sellers') }}
),

itens_por_pedido as (
    select
        order_id,
        count(distinct seller_id)                               as qtd_vendedores,
        count(order_item_id)                                    as qtd_itens,
        sum(price)                                              as valor_produtos,
        sum(freight_value)                                      as valor_frete,
        case
            when count(distinct seller_id) = 1 then min(seller_id)
            else null
        end                                                     as seller_id
    from {{ ref('olist__order_items') }}
    group by order_id
),

review_mais_recente as (
    select
        order_id,
        review_score,
        answered_at as review_answered_at
    from (
        select
            order_id,
            review_score,
            answered_at,
            row_number() over (
                partition by order_id
                order by answered_at desc
            ) as rn
        from {{ ref('olist__order_reviews') }}
    ) ranked
    where rn = 1
),

final as (
    select
        o.order_id,
        o.customer_id,
        c.customer_unique_id,
        c.state                                                 as customer_state,
        o.order_status,
        o.purchased_at,
        o.approved_at,
        o.carrier_delivered_at,
        o.customer_delivered_at,
        o.estimated_delivery_at,

        i.seller_id,
        s.state                                                 as seller_state,
        (i.qtd_vendedores > 1)                                  as multi_vendedor,
        i.qtd_itens,
        i.valor_produtos,
        i.valor_frete,

        r.review_score,
        r.review_answered_at,

        extract(epoch from (o.approved_at        - o.purchased_at))          / 86400.0  as tempo_aprovacao_dias,
        extract(epoch from (o.carrier_delivered_at - o.approved_at))         / 86400.0  as tempo_postagem_dias,
        extract(epoch from (o.customer_delivered_at - o.carrier_delivered_at)) / 86400.0 as tempo_transporte_dias,
        extract(epoch from (o.customer_delivered_at - o.purchased_at))       / 86400.0  as lead_time_total_dias,
        extract(epoch from (o.customer_delivered_at - o.estimated_delivery_at)) / 86400.0 as atraso_entrega_dias,
        (o.customer_delivered_at > o.estimated_delivery_at)                             as atrasado,
        (r.review_score <= 2)                                                           as nota_baixa

    from orders o
    left join customers c
        on o.customer_id = c.customer_id
    left join itens_por_pedido i
        on o.order_id = i.order_id
    left join sellers s
        on i.seller_id = s.seller_id
    left join review_mais_recente r
        on o.order_id = r.order_id
)

select * from final
