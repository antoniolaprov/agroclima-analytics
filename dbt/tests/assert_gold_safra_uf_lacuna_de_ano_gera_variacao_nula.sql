-- gold_safra_uf nao deve calcular variacao ano a ano quando o ano anterior
-- no lag nao e o ano imediatamente anterior. DF/soja pula 2023 no seed de
-- desenvolvimento (scripts/seed_bronze_dev.py); sem a guarda, a linha de
-- 2024 encontraria 2022 como "anterior" e produziria uma variacao de dois
-- anos rotulada como ano a ano. O teste falha (retorna linha) se essa linha
-- tiver var_producao_aa ou var_rendimento_aa preenchidas.
select uf, cultura, ano, var_producao_aa, var_rendimento_aa
from {{ ref('gold_safra_uf') }}
where uf = 'DF'
  and cultura = 'soja'
  and ano = 2024
  and (var_producao_aa is not null or var_rendimento_aa is not null)
