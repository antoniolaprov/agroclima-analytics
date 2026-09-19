with mensal as (
    select
        uf,
        year(data)  as ano,
        month(data) as mes,
        year(data) * 12 + month(data)            as mes_indice,
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

-- temp_media_movel_3m usa "range" (nao "rows") sobre mes_indice: a janela
-- inclui apenas meses cujo indice esta a ate 2 do mes atual, entao um mes
-- ausente encolhe a janela em vez de puxar um mes nao adjacente para dentro
-- da "media de 3 meses" (mesmo problema ja corrigido em var_*_aa de
-- gold_safra_uf, aqui resolvido pelo tipo de frame em vez de lag/case).
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
        partition by m.uf order by m.mes_indice range between 2 preceding and current row
    ) as temp_media_movel_3m,
    m.temp_media - n.temp_normal     as anomalia_temp,
    m.precipitacao - n.precip_normal as anomalia_precip
from mensal m
inner join normais n on n.uf = m.uf and n.mes = m.mes
