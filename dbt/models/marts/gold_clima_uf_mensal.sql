with mensal as (
    select
        uf,
        year(data)  as ano,
        month(data) as mes,
        avg(temp_media)                          as temp_media,
        max(temp_max)                            as temp_max,
        min(temp_min)                            as temp_min,
        sum(precipitacao)                        as precipitacao,
        count(distinct case when precipitacao = 0 then data end) as dias_sem_chuva,
        count(distinct cd_estacao)               as n_estacoes
    from {{ ref('stg_clima_diario') }}
    group by 1, 2, 3
),

normais as (
    select uf, mes, avg(temp_media) as temp_normal, avg(precipitacao) as precip_normal
    from mensal
    group by 1, 2
)

select
    m.uf,
    m.ano,
    m.mes,
    m.temp_media,
    m.temp_max,
    m.temp_min,
    m.precipitacao,
    m.dias_sem_chuva,
    m.n_estacoes,
    avg(m.temp_media) over (
        partition by m.uf order by m.ano, m.mes rows between 2 preceding and current row
    ) as temp_media_movel_3m,
    m.temp_media - n.temp_normal     as anomalia_temp,
    m.precipitacao - n.precip_normal as anomalia_precip
from mensal m
inner join normais n on n.uf = m.uf and n.mes = m.mes
