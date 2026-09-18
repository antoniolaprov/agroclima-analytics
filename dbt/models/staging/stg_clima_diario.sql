with por_dia as (
    select
        h.cd_estacao,
        e.uf,
        h.data,
        avg(h.temperatura)      as temp_media,
        max(h.temperatura_max)  as temp_max,
        min(h.temperatura_min)  as temp_min,
        sum(h.precipitacao)     as precipitacao,
        avg(h.umidade)          as umidade_media,
        count(h.temperatura)    as horas_observadas
    from {{ ref('stg_clima_horario') }} h
    inner join {{ ref('stg_estacoes') }} e on e.cd_estacao = h.cd_estacao
    group by 1, 2, 3
)
select *
from por_dia
where horas_observadas >= 18
