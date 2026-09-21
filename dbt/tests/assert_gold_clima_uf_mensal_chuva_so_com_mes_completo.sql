-- A chuva do mes so e publicada quando todos os dias do mes tem medicao em
-- alguma estacao da UF. Um mes com dias sem nenhuma medicao somaria so parte
-- da chuva e pareceria um mes seco.
with dias_medidos as (
    select uf, year(data) as ano, month(data) as mes, count(distinct data) as dias
    from {{ ref('stg_clima_diario') }}
    where precipitacao is not null
    group by 1, 2, 3
)

select g.uf, g.ano, g.mes, g.precipitacao, coalesce(d.dias, 0) as dias_medidos
from {{ ref('gold_clima_uf_mensal') }} g
left join dias_medidos d on d.uf = g.uf and d.ano = g.ano and d.mes = g.mes
where g.precipitacao is not null
  and coalesce(d.dias, 0) < day(last_day(make_date(g.ano, g.mes, 1)))
