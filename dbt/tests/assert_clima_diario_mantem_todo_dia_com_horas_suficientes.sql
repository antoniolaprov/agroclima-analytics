-- Todo dia de estacao com pelo menos 18 horas de temperatura em
-- stg_clima_horario precisa chegar a stg_clima_diario, independentemente da
-- situacao da estacao no catalogo: uma estacao desativada depois continua com
-- historico valido do periodo em que operou.
with esperado as (
    select cd_estacao, data
    from {{ ref('stg_clima_horario') }}
    group by 1, 2
    having count(temperatura) >= 18
)

select e.cd_estacao, e.data
from esperado e
left join {{ ref('stg_clima_diario') }} d
    on d.cd_estacao = e.cd_estacao and d.data = e.data
where d.cd_estacao is null
