select
    uf_codigo,
    uf_nome,
    cultura,
    cast(periodo as integer) as ano,
    max(case when variavel = '8331' then valor end) as area_plantada,
    max(case when variavel = '216'  then valor end) as area_colhida,
    max(case when variavel = '214'  then valor end) as producao,
    max(case when variavel = '112'  then valor end) as rendimento
from {{ source('bronze', 'pam') }}
group by 1, 2, 3, 4
