-- Sanity check do date shift (SPEC 01B).
-- Falha se qualquer pedido entregue tiver customer_delivered_at < purchased_at.
select *
from {{ ref('ecommerce__pedidos') }}
where lead_time_total_dias < 0
