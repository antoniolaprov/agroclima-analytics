-- A LSPA publica milho em dois ciclos (codigos 39441 e 39442, primeira e
-- segunda safra) que precisam ser somados antes de comparar com o total anual
-- da PAM. A comparacao e feita no total nacional: por UF, a estimativa de
-- dezembro da LSPA e o censo da PAM divergem de verdade em estados de producao
-- pequena (mais de 100% no AM e em PE em 2022), enquanto no total do pais
-- ficaram a menos de 1% em 2022-2025. Um ciclo perdido no mapeamento tiraria
-- dezenas de pontos percentuais do total, bem acima da tolerancia de 5%.
with lspa_anual as (
    select ano, sum(producao) as producao_lspa
    from {{ ref('stg_lspa') }}
    where cultura = 'milho' and mes = 12
    group by 1
),

pam_anual as (
    select ano, sum(producao) as producao_pam
    from {{ ref('stg_pam') }}
    where cultura = 'milho'
    group by 1
)

select
    p.ano,
    p.producao_pam,
    l.producao_lspa,
    abs(l.producao_lspa - p.producao_pam) / p.producao_pam as divergencia
from pam_anual p
inner join lspa_anual l on l.ano = p.ano
where p.producao_pam > 0
  and abs(l.producao_lspa - p.producao_pam) / p.producao_pam > 0.05
