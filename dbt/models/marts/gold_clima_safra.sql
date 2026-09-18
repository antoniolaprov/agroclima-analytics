with ciclo as (
    select * from {{ ref('ciclo_cultura') }}
),

meses_do_ciclo as (
    select
        c.cultura,
        m.uf,
        case when c.mes_inicio > c.mes_fim and m.mes >= c.mes_inicio
             then m.ano + 1
             else m.ano
        end as ano_safra,
        m.precipitacao,
        m.temp_media,
        m.n_estacoes
    from {{ ref('gold_clima_uf_mensal') }} m
    cross join ciclo c
    where (c.mes_inicio <= c.mes_fim and m.mes between c.mes_inicio and c.mes_fim)
       or (c.mes_inicio >  c.mes_fim and (m.mes >= c.mes_inicio or m.mes <= c.mes_fim))
),

agregado as (
    select
        uf,
        cultura,
        ano_safra as ano,
        sum(precipitacao) as precip_ciclo,
        avg(temp_media)   as temp_media_ciclo,
        min(n_estacoes)   as n_estacoes
    from meses_do_ciclo
    group by 1, 2, 3
)

select
    s.uf,
    s.cultura,
    s.ano,
    s.rendimento,
    a.precip_ciclo,
    a.temp_media_ciclo,
    a.n_estacoes
from {{ ref('gold_safra_uf') }} s
inner join agregado a on a.uf = s.uf and a.cultura = s.cultura and a.ano = s.ano
where s.rendimento is not null
