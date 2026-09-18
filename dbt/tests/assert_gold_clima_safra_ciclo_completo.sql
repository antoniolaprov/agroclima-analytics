-- gold_clima_safra so deve publicar safras com o ciclo completo: nenhuma
-- linha deve ter meses_observados diferente de meses_esperados. O teste
-- falha (retorna linha) se essa garantia for violada.
select uf, cultura, ano, meses_observados, meses_esperados
from {{ ref('gold_clima_safra') }}
where meses_observados <> meses_esperados
