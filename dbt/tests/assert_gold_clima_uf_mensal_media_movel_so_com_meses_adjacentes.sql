-- temp_media_movel_3m deve ser a media apenas dos meses que caem nos 3 meses
-- corridos ate o atual. Recalcula a janela por indice de mes e compara: um mes
-- ausente deve encolher a janela, nunca puxar um mes mais antigo para dentro.
with m as (
    select uf, ano, mes, ano * 12 + mes as mes_indice, temp_media, temp_media_movel_3m
    from {{ ref('gold_clima_uf_mensal') }}
),

recalculado as (
    select a.uf, a.ano, a.mes, a.temp_media_movel_3m, avg(b.temp_media) as media_esperada
    from m a
    inner join m b
        on b.uf = a.uf and b.mes_indice between a.mes_indice - 2 and a.mes_indice
    group by 1, 2, 3, 4
)

select *
from recalculado
where abs(temp_media_movel_3m - media_esperada) > 0.001
