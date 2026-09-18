select
    uf_codigo,
    uf_nome,
    cultura,
    safra_ciclo,
    cast(substr(periodo, 1, 4) as integer) as ano,
    cast(substr(periodo, 5, 2) as integer) as mes,
    max(case when variavel = '109' then valor end) as area_plantada,
    max(case when variavel = '35'  then valor end) as producao,
    max(case when variavel = '36'  then valor end) as rendimento
from {{ source('bronze', 'lspa') }}
group by 1, 2, 3, 4, 5, 6
