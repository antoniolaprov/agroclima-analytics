-- A LSPA publica milho em dois ciclos (codigos 39441 e 39442, primeira e
-- segunda safra) que precisam ser somados antes de comparar com o total
-- anual da PAM. O teste falha (retorna linha) se a producao de dezembro da
-- LSPA (estimativa final do ano) divergir da PAM em mais de 15% para o
-- mesmo uf_codigo/ano.
with lspa_anual as (
    select uf_codigo, ano, sum(producao) as producao_lspa
    from {{ ref('stg_lspa') }}
    where cultura = 'milho' and mes = 12
    group by 1, 2
),

pam_anual as (
    select uf_codigo, ano, producao as producao_pam
    from {{ ref('stg_pam') }}
    where cultura = 'milho'
)

select
    p.uf_codigo,
    p.ano,
    p.producao_pam,
    l.producao_lspa,
    abs(l.producao_lspa - p.producao_pam) / nullif(p.producao_pam, 0) as divergencia
from pam_anual p
inner join lspa_anual l on l.uf_codigo = p.uf_codigo and l.ano = p.ano
where p.producao_pam > 0
  and abs(l.producao_lspa - p.producao_pam) / p.producao_pam > 0.15
