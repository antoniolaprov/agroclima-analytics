with ciclo as (
    select
        *,
        case when mes_inicio <= mes_fim
             then mes_fim - mes_inicio + 1
             else (12 - mes_inicio + 1) + mes_fim
        end as meses_esperados
    from {{ ref('ciclo_cultura') }}
),

meses_do_ciclo as (
    select
        c.cultura,
        c.meses_esperados,
        m.uf,
        case when c.mes_inicio > c.mes_fim and m.mes >= c.mes_inicio
             then m.ano + 1
             else m.ano
        end as ano_safra,
        m.mes,
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
        sum(precipitacao)    as precip_ciclo,
        avg(temp_media)      as temp_media_ciclo,
        min(n_estacoes)      as n_estacoes,
        count(distinct mes)  as meses_observados,
        max(meses_esperados) as meses_esperados
    from meses_do_ciclo
    group by 1, 2, 3
)

-- So publica safras com o ciclo completo: uma safra com meses faltando no
-- meio do ciclo (por exemplo o ano-safra na borda da janela climatica
-- disponivel) teria precip_ciclo/temp_media_ciclo calculados sobre uma
-- fracao do ciclo, mas apresentados como se fossem o total - um numero
-- errado e mais enganoso que a ausencia da linha. meses_observados e
-- meses_esperados ficam expostos para quem quiser entender por que um ano
-- nao aparece.
select
    s.uf,
    s.cultura,
    s.ano,
    s.rendimento,
    a.precip_ciclo,
    a.temp_media_ciclo,
    a.n_estacoes,
    a.meses_observados,
    a.meses_esperados
from {{ ref('gold_safra_uf') }} s
inner join agregado a on a.uf = s.uf and a.cultura = s.cultura and a.ano = s.ano
where s.rendimento is not null
  and a.meses_observados = a.meses_esperados
