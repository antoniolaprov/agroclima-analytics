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
)

select
    *,
    100.0 * (producao / nullif(lag(producao) over (partition by uf, cultura order by ano), 0) - 1)
        as var_producao_aa,
    100.0 * (rendimento / nullif(lag(rendimento) over (partition by uf, cultura order by ano), 0) - 1)
        as var_rendimento_aa
from base
