-- A UF e agregada em dois passos: primeiro o dia (media entre as estacoes que
-- reportaram), depois o mes. Agregar direto por mes somaria a chuva de todas as
-- estacoes do estado e contaria como seco qualquer dia em que uma unica estacao
-- ficou sem chuva.
with diario_uf as (
    select
        uf,
        data,
        avg(temp_media)   as temp_media,
        max(temp_max)     as temp_max,
        min(temp_min)     as temp_min,
        avg(precipitacao) as precipitacao
    from {{ ref('stg_clima_diario') }}
    group by 1, 2
),

estacoes_no_mes as (
    select uf, year(data) as ano, month(data) as mes, count(distinct cd_estacao) as n_estacoes
    from {{ ref('stg_clima_diario') }}
    group by 1, 2, 3
),

mensal as (
    select
        d.uf,
        year(d.data)  as ano,
        month(d.data) as mes,
        year(d.data) * 12 + month(d.data)       as mes_indice,
        avg(d.temp_media)                       as temp_media,
        max(d.temp_max)                         as temp_max,
        min(d.temp_min)                         as temp_min,
        -- Chuva e dias secos so com o mes inteiro medido: com dias sem nenhuma
        -- medicao na UF, a soma cobriria so parte do mes e pareceria seca.
        -- Dia seco: media da UF abaixo de 1 mm, o limiar usual de dia sem chuva.
        case when count(d.precipitacao) = day(last_day(min(d.data)))
             then sum(d.precipitacao)
        end                                     as precipitacao,
        case when count(d.precipitacao) = day(last_day(min(d.data)))
             then count(case when d.precipitacao < 1 then 1 end)
        end                                     as dias_sem_chuva,
        max(e.n_estacoes)                       as n_estacoes
    from diario_uf d
    inner join estacoes_no_mes e
        on e.uf = d.uf and e.ano = year(d.data) and e.mes = month(d.data)
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
