-- A precipitacao mensal de uma UF e a media entre as estacoes, nao a soma:
-- somar as dezenas de estacoes do RS daria dezenas de vezes a chuva real. Em cada dia
-- a media entre estacoes nunca passa da maior leitura do dia, entao o total do
-- mes nao pode passar da soma dos maximos diarios.
with maximo_diario as (
    select uf, data, max(precipitacao) as mm
    from {{ ref('stg_clima_diario') }}
    group by 1, 2
),

teto_mensal as (
    select uf, year(data) as ano, month(data) as mes, sum(mm) as teto
    from maximo_diario
    group by 1, 2, 3
)

select g.uf, g.ano, g.mes, g.precipitacao, t.teto
from {{ ref('gold_clima_uf_mensal') }} g
inner join teto_mensal t on t.uf = g.uf and t.ano = g.ano and t.mes = g.mes
where g.precipitacao > t.teto + 0.001
