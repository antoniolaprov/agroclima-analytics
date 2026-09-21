-- var_*_aa so pode vir preenchida quando existe a linha do ano imediatamente
-- anterior para a mesma uf/cultura. A PAM pode ter anos ausentes numa serie;
-- sem essa garantia, lag() compararia com o ano nao adjacente mais proximo e
-- a variacao seria rotulada como ano a ano sem ser.
select s.uf, s.cultura, s.ano, s.var_producao_aa, s.var_rendimento_aa
from {{ ref('gold_safra_uf') }} s
left join {{ ref('gold_safra_uf') }} p
    on p.uf = s.uf and p.cultura = s.cultura and p.ano = s.ano - 1
where p.ano is null
  and (s.var_producao_aa is not null or s.var_rendimento_aa is not null)
