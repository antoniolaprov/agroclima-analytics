with base as (
    select
        d.uf,
        p.uf_codigo,
        p.cultura,
        p.ano,
        p.area_plantada,
        p.area_colhida,
        p.producao,
        p.rendimento
    from {{ ref('stg_pam') }} p
    inner join {{ ref('dim_uf') }} d on d.uf_codigo = p.uf_codigo
),

com_lag as (
    select
        *,
        lag(ano) over (partition by uf, cultura order by ano)        as ano_anterior,
        lag(producao) over (partition by uf, cultura order by ano)   as producao_anterior,
        lag(rendimento) over (partition by uf, cultura order by ano) as rendimento_anterior
    from base
)

-- var_*_aa so e calculada quando o lag encontrou o ano imediatamente
-- anterior (ano_anterior = ano - 1). A PAM e um censo anual e uma serie
-- uf/cultura pode ter anos ausentes; sem essa checagem, lag() comparia
-- com o ano nao adjacente mais proximo e a variacao seria rotulada como
-- "ano a ano" sem ser.
select
    uf,
    uf_codigo,
    cultura,
    ano,
    area_plantada,
    area_colhida,
    producao,
    rendimento,
    case when ano_anterior = ano - 1
         then 100.0 * (producao / nullif(producao_anterior, 0) - 1)
    end as var_producao_aa,
    case when ano_anterior = ano - 1
         then 100.0 * (rendimento / nullif(rendimento_anterior, 0) - 1)
    end as var_rendimento_aa
from com_lag
